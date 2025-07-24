# Shopify Inventory Location Sync

This script connects all product variants (including untracked items) to a specific Shopify location via the Admin API. It supports restarts, batch testing, and filtering for only untracked variants.

---

## 🔧 Requirements

- Python 3.7+
- A [Shopify Admin API access token](https://shopify.dev/docs/api/admin-rest#authentication)
- The target location ID from your Shopify store
- `python-dotenv` for environment variable loading

---

## 🧪 Installation

1. Clone this repo.
```bash
git clone https://github.com/your-org/shopify-inventory-location-sync.git
cd shopify-inventory-location-sync
```
2. Install dependencies:
`pip install -r requirements.txt`

Or install manually:

`pip install requests python-dotenv`

## 🔐 Environment Configuration

This script uses a .env file for credentials and options. Create a .env file based on the provided template:

`cp .env.example .env`

Then edit `.env`:
```env
SHOP_NAME=your-shop.myshopify.com
ACCESS_TOKEN=your-access-token
TARGET_LOCATION_ID=85972877548
PRODUCT_LIMIT=5
ONLY_PROCESS_UNTRACKED=False
```

## 🚀 Usage

Run the script from the command line:

```python inventory_sync.py```

## 🔄 Restart-Safe
If you stop the script, it will resume next time by skipping already-processed variants listed in 

`inventory_update_log.txt`.

## 🧪 Test Mode

Start with small batches:
PRODUCT_LIMIT=1
