*** Settings ***
Documentation    Test suite generated from session saucedemo containing 1 test case for web automation.
Library         Browser
Test Tags       automated    generated    web

*** Test Cases ***
Saucedemo 登录加购物车
    [Documentation]    Test case that performs click action, performs click action.
    New Persistent Context    F:/github/auto_robot/demo/saucedemo_profile    chromium    headless=True    url=https://www.saucedemo.com/
    Fill Text    id=user-name    standard_user
    Fill Text    id=password    secret_sauce
    Click    id=login-button    # Click on id=login-button
    Get Text    css=.title
    Click    id=add-to-cart-sauce-labs-backpack    # Click on id=add-to-cart-sauce-labs-backpack
    Get Text    css=.shopping_cart_badge
    [Teardown]    Close Browser    
