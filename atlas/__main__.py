from .conversation import Conversation


def main():
    conversation = Conversation()
    print("Atlas — assistente pessoal de viagens. Digite oi para começar ou sair para encerrar.")
    while True:
        try:
            message = input("Você: ")
        except (EOFError, KeyboardInterrupt):
            break
        if message.strip().casefold() == "sair":
            break
        print("Atlas:", conversation.reply("local-demo", message))


if __name__ == "__main__":
    main()
