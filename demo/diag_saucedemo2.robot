*** Settings ***
Library    Browser

*** Test Cases ***
Diag2 Saucedemo Profile
    New Persistent Context    F:/github/auto_robot/demo/saucedemo_profile    chromium    headless=True    url=https://www.saucedemo.com/
    ${u1}=    Get Url
    Log To Console    URL1: ${u1}
    Fill Text    id=user-name    standard_user
    Log To Console    STEP: after username
    Fill Text    id=password    secret_sauce
    Log To Console    STEP: after password
    Click    id=login-button
    Log To Console    STEP: after login
    ${u2}=    Get Url
    Log To Console    URL2: ${u2}
    ${title}=    Get Text    css=.title
    Log To Console    TITLE: ${title}
    ${cnt}=    Get Element Count    id=add-to-cart-sauce-labs-backpack
    Log To Console    ADDCART_COUNT: ${cnt}
    ${items}=    Get Element Count    css=.inventory_item
    Log To Console    ITEMS: ${items}
    ${ls}=    Evaluate JavaScript    ${None}    () => JSON.stringify(localStorage)
    Log To Console    LOCALSTORAGE: ${ls}
    ${ck}=    Get Cookie
    Log To Console    COOKIES: ${ck}
    ${bt}=    Get Text    body
    Log To Console    BODY: ${bt}
    Click    id=add-to-cart-sauce-labs-backpack
    Log To Console    STEP: clicked add to cart
    Close Browser
