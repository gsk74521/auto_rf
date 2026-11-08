"""诊断 saucedemo_profile 的状态污染：打开 inventory 页看 items / cookie / localStorage。"""
from Browser import Browser

b = Browser()
b.new_persistent_context(
    "F:/github/auto_robot/demo/saucedemo_profile",
    "chromium", headless=True, url="https://www.saucedemo.com/",
)
b.fill_text("id=user-name", "standard_user")
b.fill_text("id=password", "secret_sauce")
b.click("id=login-button")
print("URL:", b.get_url())
print("items:", b.get_element_count("css=.inventory_item"))
print("addcart:", b.get_element_count("id=add-to-cart-sauce-labs-backpack"))
for name in ("get_cookie", "get_cookies"):
    fn = getattr(b, name, None)
    if fn:
        try:
            print(f"{name}:", str(fn())[:600])
        except Exception as e:
            print(f"{name} err:", e)
try:
    print("localStorage:", b.evaluate_javascript("() => JSON.stringify(localStorage)")[:500])
except Exception as e:
    print("localStorage err:", e)
try:
    print("body_text:", b.get_text("body")[:400])
except Exception as e:
    print("body err:", e)
b.close_browser()
