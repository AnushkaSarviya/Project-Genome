from services.user_service import UserService


def main():
    service = UserService()
    user = service.create_user(1, "Alice")
    fetched = service.get_user(1)
    print(fetched)


if __name__ == "__main__":
    main()
