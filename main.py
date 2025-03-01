import requests
import os
import csv
from dotenv import load_dotenv

load_dotenv()

# Base URL for Qogita's API
QOGITA_API_URL = "https://api.qogita.com"

# Login details for user
QOGITA_EMAIL = os.getenv("QOGITA_EMAIL")
QOGITA_PASSWORD = os.getenv("QOGITA_PASSWORD")

COMPLETE_CHECKOUT = False


class QogitaApi:
    """
    Qogita API

    Utility class to abstract and simplify interactions with the Qogita API.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.auth_headers = None
        self.user = None
        self.cart_qid = None

    def login(self, email: str, password: str) -> None:
        response = self._post(
            path="/auth/login/",
            data={"email": email, "password": password}
        )
        response = response.json()

        access_token = response["accessToken"]

        self.auth_headers = {
            "Authorization": f"Bearer {access_token}",
        }

        self.user = response["user"]
        self.cart_qid = self.user["activeCartQid"]

    def search_variants(self,
                        page: int = 1,
                        size: int = 50,
                        query: str | None = None,
                        category_name: str | None = None,
                        brand_names: list[str] | None = None,
                        has_deals: bool | None = None) -> dict:

        path = f"/variants/search/?page={page}&size={size}"

        if query is not None:
            path += f"&query={query}"

        if category_name is not None:
            path += f"&category_name={category_name}"

        if brand_names is not None:
            path += f"&brand_name={'&brand_name='.join(brand_names)}"

        if has_deals is not None:
            path += f"&has_deals={has_deals}"

        response = self._get(path=path)

        return response.json()

    def get_cart(self) -> dict:
        response = self._get(path=f"/carts/{self.cart_qid}/")
        return response.json()

    def empty_cart(self):
        self._post(path=f"/carts/{self.cart_qid}/empty/")

    def add_product_to_cart(self, gtin: str, quantity: int) -> None:
        self._post(
            path=f"/carts/{self.cart_qid}/lines/",
            data={"gtin": gtin, "quantity": quantity})

    def allocate_cart(self) -> dict:
        self._post(path=f"/carts/{self.cart_qid}/optimize/")
        response = self._get(path=f"/carts/{self.cart_qid}/allocation-summary/")
        return response.json()

    def get_allocation_lines(self, page: int = 1, size: int = 50) -> dict:
        response = self._get(path=f"/carts/{self.cart_qid}/allocation-lines/?page={page}&size={size}")
        return response.json()

    def get_addresses(self, page: int = 1, size: int = 50) -> dict:
        response = self._get(path=f"/addresses/?page={page}&size={size}")
        return response.json()

    def checkout(self,
                 shipping_address_qid: str,
                 billing_address_qid: str) -> dict:

        # retrieve the checkout identifier associated to our cart
        checkout_qid = self.get_cart()["checkoutQid"]

        # update the addresses for checkout
        self._patch(
            path=f"/checkouts/{checkout_qid}/",
            data={"shippingAddressQid": shipping_address_qid, "billingAddressQid": billing_address_qid})

        # finalize checkout
        response = self._post(path=f"/checkouts/{checkout_qid}/complete/")

        return response.json()

    def _get(self, path: str, headers: dict | None = None) -> requests.Response:
        return self._call(method="get", path=path, headers=headers)

    def _post(
            self, path: str, data: dict | None = None, headers: dict | None = None
    ) -> requests.Response:
        return self._call(method="post", path=path, data=data, headers=headers)

    def _patch(
            self, path: str, data: dict | None = None, headers: dict | None = None
    ) -> requests.Response:
        return self._call(method="patch", path=path, data=data, headers=headers)

    def _delete(
            self, path: str, data: dict | None = None, headers: dict | None = None
    ) -> requests.Response:
        return self._call(method="delete", path=path, data=data, headers=headers)

    def _call(
            self,
            method: str,
            path: str,
            data: dict | None = None,
            headers: dict | None = None,
    ) -> requests.Response:
        headers = {**(headers or {}), **(self.auth_headers or {})}

        response = requests.request(
            method=method, url=f"{QOGITA_API_URL}{path}", data=data, headers=headers
        )

        response.raise_for_status()

        return response


# create the API instance
api = QogitaApi(QOGITA_API_URL)

# api.login(
#     email=QOGITA_EMAIL,
#     password=QOGITA_PASSWORD)
#
# print("Searching for products")
#
# # search products you're interested on
#
# search_response = api.search_variants(
#     page=2,
#     size=500,
#     has_deals=True
# )
# print(search_response["count"])
# variants = search_response["results"]
# print(len(variants))


def main():
    print("Logging in")

    # login using your Qogita credentials
    api.login(
        email=QOGITA_EMAIL,
        password=QOGITA_PASSWORD)

    page = 1
    results = []
    while True:
        print(f"Getting page {page}")
        search_response = api.search_variants(
            page=page,
            size=500,
            has_deals=True
        )
        next_ = search_response["next"]
        print(next_)
        results += search_response["results"]
        page += 1
        if not next_:
            break
    print(f"Total {search_response["count"]} results")
    gtins = [[item["gtin"]] for item in results]
    filename = 'output.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        # Запись строк в файл
        for row in gtins:
            writer.writerow(row)

    print(f"Done. File is accessible with name {filename}")


if __name__ == "__main__":
    main()



