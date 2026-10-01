from models.base import BaseModel


class User(BaseModel):
    """User data model."""

    def __init__(self, id: int, name: str):
        super().__init__(id)
        self.name = name

    def get_display_name(self) -> str:
        return f"User: {self.name}"
