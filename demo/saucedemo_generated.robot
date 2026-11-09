*** Settings ***
Documentation    Test suite generated from session quick containing 1 test case for web automation.
Library         Browser
Test Tags       automated    generated    web

*** Test Cases ***
Saucedemo acceptance
    [Documentation]    Test case that navigates to page, performs click action, performs click action.
    New Persistent Context    ${OUTPUTDIR}${/}browser-profile    chromium    headless=True    url=https://www.saucedemo.com/
    Evaluate JavaScript    ${None}    () => { localStorage.clear(); sessionStorage.clear(); }
    Go To    https://www.saucedemo.com/
    Fill Text    id=user-name    standard_user
    Fill Text    id=password    secret_sauce
    Click    id=login-button    # Click on id=login-button
    Get Text    css=.title    ==    Products
    Click    id=add-to-cart-sauce-labs-backpack    # Click on id=add-to-cart-sauce-labs-backpack
    Get Text    css=.shopping_cart_badge    ==    1
    [Teardown]    Close Browser    
