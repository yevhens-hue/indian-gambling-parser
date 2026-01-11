# merchants_config.py

MERCHANTS = {
    "1xbet": {
        "brand": "1xbet",
        "brand_variants": ["1xbet", "1x bet", "1xBet"],
        "official_domains": [
            "1xbet.com",
            "1xbet.xyz",
            "1x-bet.com",
            "indian.1xbet.com",
        ],
        # Креденшиалы для входа
        "credentials": {
            "username": "800913939",
            "password": "7t5bhayw",
        },
        # Селекторы для логина
        "selectors": {
            "login_button": "a[href*='login'], button.login, .login-btn, .auth-button, [data-test='login-button']",
            "username_input": "input[name='login'], input[name='username'], input[name='phone'], input[type='text'][placeholder*='login'], input[placeholder*='Login'], input[placeholder*='phone'], input[placeholder*='Phone'], input[id*='login'], input[id*='username'], input[id*='phone'], input[class*='login'], input[class*='username']",
            "password_input": "input[name='password'], input[type='password'], input[id*='password'], input[class*='password']",
            "submit_button": "button[type='submit'], button.login-submit, .submit-btn, button[class*='submit'], button[class*='enter'], [data-test='submit-button']",
            # Навигация к кэширу
            "cashier_link": "a[href*='cashier'], a[href*='deposit'], a[href*='payment'], a[href*='payments'], .cashier, .deposit, [data-test='deposit'], [data-test='cashier']",
            "cashier_button": "button[class*='cashier'], button[class*='deposit'], button[class*='payment']",
            # Кнопка "Make Deposit" (CSS селекторы без :contains)
            "make_deposit_button": "[class*='make-deposit'], [class*='deposit-button'], button[class*='deposit']",
            # Секция E-WALLETS
            "ewallets_section": "[class*='e-wallet'], [class*='ewallet'], [class*='E-WALLET'], [class*='E-WALLETS'], [id*='ewallet'], [id*='e-wallet']",
            # Селекторы провайдеров на странице кэшира
            "provider_buttons": "button[class*='provider'], button[class*='payment'], .payment-method, .provider-item, [data-provider], [data-payment], img[alt*='payment'], img[alt*='Payment'], .payment-option, .payment-provider, [class*='payment-method'], [class*='provider']",
            "provider_links": "a[href*='provider'], a[class*='provider'], a[class*='payment'], .provider-link, a[data-provider], a[data-payment]",
        },
        # Тип аккаунта: admin/agent/player/merchant-ops
        "account_type": "player",
        # Прямой URL страницы кэшира (если известен)
        "cashier_url": "https://indian.1xbet.com/en/office/recharge",
        # Данные для заполнения форм провайдеров
        "provider_form_data": {
            "upi_id": "kapil.ss17@icici",
            "phone_number": "+918925242020",
            "aadhaar": "571517312306",
            "fullname": "kapil sharma",
        },
        # Минимальная сумма для депозита (по умолчанию 300 INR - минимальная сумма на 1xbet)
        "default_amount": "300",
    },

    "dafabet": {
        "brand": "dafabet",
        "brand_variants": ["dafabet", "dafa bet"],
        "official_domains": [
            "dafabet.com",
            "dafabet.net"
        ],
        "credentials": {
            "username": "",  # Заполнить при необходимости
            "password": "",  # Заполнить при необходимости
        },
        "selectors": {
            "login_button": "a[href*='login'], button.login, .login-btn",
            "username_input": "input[name='username'], input[name='login'], input[type='text'][placeholder*='username']",
            "password_input": "input[name='password'], input[type='password']",
            "submit_button": "button[type='submit'], button.login-submit, .submit-btn",
            "cashier_link": "a[href*='cashier'], a[href*='deposit'], a[href*='payment'], .cashier, .deposit",
            "cashier_button": "button[class*='cashier'], button[class*='deposit']",
            "provider_buttons": "button[class*='provider'], .payment-method, .provider-item, [data-provider]",
            "provider_links": "a[href*='provider'], a[class*='provider'], .provider-link",
        },
        "account_type": "player",
    },

    "octabroker": {
        "brand": "octabroker",
        "brand_variants": ["octabroker", "octa broker", "octa"],
        "official_domains": [
            "octabroker.com",
            "www.octabroker.com",
        ],
        # Креденшиалы для входа
        "credentials": {
            "username": "kapil.ss17@yahoo.in",
            "password": "Butterfly@24",
        },
        # Селекторы для логина
        "selectors": {
            "login_button": "a[href*='login'], button.login, .login-btn, .auth-button, [data-test='login-button'], button:has-text('Log in'), button:has-text('Sign in'), a:has-text('Log in'), a:has-text('Sign in')",
            "username_input": "input[name='email'], input[name='username'], input[name='login'], input[type='email'], input[type='text'][placeholder*='email' i], input[placeholder*='Email' i], input[placeholder*='username' i], input[placeholder*='Username' i], input[id*='email'], input[id*='username'], input[id*='login'], input[class*='email'], input[class*='username']",
            "password_input": "input[name='password'], input[type='password'], input[id*='password'], input[class*='password']",
            "submit_button": "button[type='submit'], button.login-submit, .submit-btn, button[class*='submit'], button[class*='enter'], [data-test='submit-button'], button:has-text('Log in'), button:has-text('Sign in'), button:has-text('Login')",
            # Навигация к кэширу/депозиту
            "cashier_link": "a[href*='deposit'], a[href*='payment'], a[href*='payments'], a[href*='cashier'], .cashier, .deposit, [data-test='deposit'], [data-test='cashier'], a:has-text('Deposit'), a:has-text('Fund')",
            "cashier_button": "button[class*='cashier'], button[class*='deposit'], button[class*='payment'], button:has-text('Deposit'), button:has-text('Fund')",
            # Кнопка "Make Deposit" или "Deposit"
            "make_deposit_button": "[class*='make-deposit'], [class*='deposit-button'], button[class*='deposit'], button:has-text('Deposit'), button:has-text('Make Deposit')",
            # Секция платежных методов (может быть E-WALLETS, Payment Methods, и т.д.)
            "ewallets_section": "[class*='payment-method'], [class*='payment-methods'], [class*='e-wallet'], [class*='ewallet'], [class*='E-WALLET'], [class*='E-WALLETS'], [id*='payment'], [id*='ewallet'], [id*='e-wallet'], [class*='deposit-method']",
            # Селекторы провайдеров на странице депозита
            "provider_buttons": "button[class*='provider'], button[class*='payment'], .payment-method, .provider-item, [data-provider], [data-payment], img[alt*='payment'], img[alt*='Payment'], .payment-option, .payment-provider, [class*='payment-method'], [class*='provider'], button:has-text('Pay'), button:has-text('Select')",
            "provider_links": "a[href*='provider'], a[class*='provider'], a[class*='payment'], .provider-link, a[data-provider], a[data-payment], a:has-text('Pay')",
        },
        # Тип аккаунта: trader/investor
        "account_type": "trader",
        # Прямой URL страницы депозита (если известен, иначе будет найден автоматически)
        "cashier_url": None,  # Будет найден автоматически
        # Данные для заполнения форм провайдеров
        "provider_form_data": {
            "upi_id": "kapil.ss17@icici",
            "phone_number": "+918925242020",
            "aadhaar": "571517312306",
            "fullname": "kapil sharma",
        },
        # Минимальная сумма для депозита (нужно уточнить для Octa Broker)
        "default_amount": "100",
    },

    "olymptrade": {
        "brand": "olymptrade",
        "brand_variants": ["olymptrade", "olympic trade", "olympic"],
        "official_domains": [
            "olymptrade.com",
            "www.olymptrade.com",
        ],
        # Креденшиалы для входа
        "credentials": {
            "username": "rencruise961@gmail.com",
            "password": "Ren@Cruise01",
        },
        # Селекторы для логина
        "selectors": {
            "login_button": "button:has-text('LogIn'), button:has-text('Log in'), button:has-text('Login'), a:has-text('LogIn'), a:has-text('Log in'), a:has-text('Login'), [class*='login'], [id*='login']",
            # Вкладка "Вход" (нужно переключиться перед заполнением полей, если открыта вкладка "Регистрация")
            "login_tab": "button:has-text('Вход'), button:has-text('Войти'), a:has-text('Вход'), a:has-text('Войти'), [class*='login-tab'], [id*='login-tab'], [data-tab='login'], [role='tab']:has-text('Вход'), [role='tab']:has-text('Войти'), button:has-text('Login'), button:has-text('Log In'), a:has-text('Login'), a:has-text('Log In'), [role='tab']:has-text('Login'), [role='tab']:has-text('Log In')",
            "username_input": "input[name='email'], input[type='email'], input[name='username'], input[placeholder*='email' i], input[placeholder*='Email' i], input[id*='email'], input[class*='email']",
            "password_input": "input[name='password'], input[type='password'], input[id*='password'], input[class*='password']",
            "submit_button": "button[type='submit'], button:has-text('LogIn'), button:has-text('Log in'), button:has-text('Login'), [class*='submit'], [class*='login-button']",
            # Навигация: Payments -> Deposit -> Next
            "payments_button": "button:has-text('Payments'), a:has-text('Payments'), [class*='payment'], [id*='payment'], button:has-text('Payment')",
            "deposit_button": "button:has-text('Deposit'), a:has-text('Deposit'), [class*='deposit'], [id*='deposit']",
            "next_button": "button:has-text('Next'), button:has-text('NEXT'), [class*='next'], [id*='next']",
            # Кнопка "Proceed to payment"
            "proceed_button": "button:has-text('Proceed to payment'), button:has-text('Proceed'), button:has-text('PROCEED'), [class*='proceed'], [id*='proceed']",
            # Поля формы
            "first_name_input": "input[name*='first' i], input[name*='firstName' i], input[placeholder*='first' i], input[id*='first' i], input[class*='first' i]",
            "last_name_input": "input[name*='last' i], input[name*='lastName' i], input[name*='surname' i], input[placeholder*='last' i], input[id*='last' i], input[class*='last' i], input[class*='surname' i]",
            "phone_input": "input[name*='phone' i], input[type='tel'], input[placeholder*='phone' i], input[id*='phone' i], input[class*='phone' i]",
            "upi_id_input": "input[name*='upi' i], input[placeholder*='upi' i], input[id*='upi' i], input[class*='upi' i]",
        },
        # Тип аккаунта
        "account_type": "trader",
        # Прямой URL страницы (платформа)
        "cashier_url": "https://olymptrade.com/platform",
        # Данные для заполнения форм
        "provider_form_data": {
            "first_name": "kapil",
            "last_name": "Sharma",
            "phone_number": "8925242020",
            "upi_id": "kapil.ss17@icici",
        },
        # Минимальная сумма для депозита
        "default_amount": "100",
    },

    "1win": {
        "brand": "1win",
        "brand_variants": ["1win", "1 win"],
        "official_domains": [
            "1win.com",
            "1win.in",
            "www.1win.com",
        ],
        # Креденшиалы для входа
        "credentials": {
            "username": "",  # Заполнить при необходимости
            "password": "",  # Заполнить при необходимости
        },
        # Селекторы для логина
        "selectors": {
            "login_button": "a[href*='login'], button.login, .login-btn, .auth-button, [data-test='login-button']",
            "username_input": "input[name='login'], input[name='username'], input[name='email'], input[name='phone'], input[type='text'][placeholder*='login'], input[type='email'], input[placeholder*='email'], input[placeholder*='phone'], input[id*='login'], input[id*='username'], input[id*='email'], input[id*='phone'], input[class*='login'], input[class*='username'], input[class*='email']",
            "password_input": "input[name='password'], input[type='password'], input[id*='password'], input[class*='password']",
            "submit_button": "button[type='submit'], button.login-submit, .submit-btn, button[class*='submit'], button[class*='enter'], [data-test='submit-button']",
            # Навигация к кэширу
            "cashier_link": "a[href*='cashier'], a[href*='deposit'], a[href*='payment'], a[href*='payments'], .cashier, .deposit, [data-test='deposit'], [data-test='cashier']",
            "cashier_button": "button[class*='cashier'], button[class*='deposit'], button[class*='payment']",
            # Кнопка "Make Deposit" или "Deposit"
            "make_deposit_button": "[class*='make-deposit'], [class*='deposit-button'], button[class*='deposit'], button:has-text('Deposit')",
            # Секция E-WALLETS или Payment Methods
            "ewallets_section": "[class*='payment-method'], [class*='payment-methods'], [class*='e-wallet'], [class*='ewallet'], [class*='E-WALLET'], [class*='E-WALLETS'], [id*='ewallet'], [id*='e-wallet'], [id*='payment']",
            # Селекторы провайдеров на странице кэшира
            "provider_buttons": "button[class*='provider'], button[class*='payment'], .payment-method, .provider-item, [data-provider], [data-payment], img[alt*='payment'], img[alt*='Payment'], .payment-option, .payment-provider, [class*='payment-method'], [class*='provider']",
            "provider_links": "a[href*='provider'], a[class*='provider'], a[class*='payment'], .provider-link, a[data-provider], a[data-payment]",
        },
        # Тип аккаунта: FTD (First Time Deposit) или STD (Standard Deposit)
        "account_type": "FTD",  # Можно менять на STD
        # Прямой URL страницы кэшира (если известен)
        "cashier_url": None,  # Будет найден автоматически
        # Данные для заполнения форм провайдеров
        "provider_form_data": {
            "upi_id": "8750270451@okbizaxis",
            "phone_number": "+918750270451",
            "fullname": "manish",
        },
        # Минимальная сумма для депозита
        "default_amount": "500",
    }
}

