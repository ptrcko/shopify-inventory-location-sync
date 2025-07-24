import requests
import time
import logging

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

SHOP_NAME = os.getenv("SHOP_NAME")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
TARGET_LOCATION_ID = int(os.getenv("TARGET_LOCATION_ID"))
PRODUCT_LIMIT = int(os.getenv("PRODUCT_LIMIT")) if os.getenv("PRODUCT_LIMIT") else None
ONLY_PROCESS_UNTRACKED = os.getenv("ONLY_PROCESS_UNTRACKED", "False").lower() == "true"

LOG_FILE = "inventory_update_log.txt"

# ==== LOGGING SETUP ====
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')
print(f"Logging to {LOG_FILE}")

# ==== HEADERS ====
HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# ==== BASE URL ====
BASE_URL = f"https://{SHOP_NAME}/admin/api/2023-10"


# ==== LOAD PROCESSED VARIANTS ====
def load_processed_variant_ids():
    processed_ids = set()
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                if "variant " in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "variant" and i + 1 < len(parts):
                            try:
                                variant_id = int(parts[i + 1])
                                processed_ids.add(variant_id)
                            except ValueError:
                                continue
    except FileNotFoundError:
        pass
    return processed_ids


# ==== API CALLS ====

def get_all_products(limit=None):
    products = []
    url = f"{BASE_URL}/products.json?limit=250"
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get("products", [])
        products.extend(data)

        if limit and len(products) >= limit:
            return products[:limit]

        link = response.headers.get("Link", "")
        if 'rel="next"' in link:
            url = link.split(";")[0].strip("<> ")
        else:
            break

    return products


def get_inventory_levels(inventory_item_id):
    url = f"{BASE_URL}/inventory_levels.json?inventory_item_ids={inventory_item_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("inventory_levels", [])


def is_inventory_tracked(inventory_item_id):
    url = f"{BASE_URL}/inventory_items/{inventory_item_id}.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    item = response.json().get("inventory_item", {})
    return item.get("tracked", False)


def is_item_connected_to_location(inventory_item_id, location_id):
    try:
        levels = get_inventory_levels(inventory_item_id)
        return any(l["location_id"] == location_id for l in levels)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            # Untracked item, no inventory levels available
            return False
        raise


def connect_inventory_item_to_location(inventory_item_id):
    url = f"{BASE_URL}/inventory_levels/connect.json"
    payload = {
        "location_id": TARGET_LOCATION_ID,
        "inventory_item_id": inventory_item_id,
        "relocate_if_necessary": True
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


# ==== MAIN PROCESSING ====

def process_products(products):
    processed_ids = load_processed_variant_ids()
    print(f"Skipping {len(processed_ids)} already processed variants.")

    for product in products:
        for variant in product.get("variants", []):
            inventory_item_id = variant.get("inventory_item_id")
            variant_id = variant.get("id")
            if not inventory_item_id or not variant_id:
                continue

            if variant_id in processed_ids:
                print(f"Skipping already processed variant {variant_id}")
                continue

            try:
                tracked = is_inventory_tracked(inventory_item_id)

                if ONLY_PROCESS_UNTRACKED and tracked:
                    print(f"Skipping tracked variant {variant_id}")
                    continue

                if is_item_connected_to_location(inventory_item_id, TARGET_LOCATION_ID):
                    print(f"Already connected {variant_id}")
                    continue  # already connected

                connect_inventory_item_to_location(inventory_item_id)

                msg = (f"Processed variant {variant_id} of product '{product['title']}' "
                    f"to location {TARGET_LOCATION_ID} (tracked={tracked})")
                print(msg)
                logging.info(msg)

                time.sleep(0.2)

            except Exception as e:
                err = f"Error processing variant {variant_id} of '{product['title']}': {str(e)}"
                print(err)
                logging.error(err)



def main():
    print(f"Fetching products (limit: {PRODUCT_LIMIT or 'all'})...")
    products = get_all_products(limit=PRODUCT_LIMIT)
    print(f"Processing {len(products)} products...")
    process_products(products)
    print("Update complete.")


if __name__ == "__main__":
    main()