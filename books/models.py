from django.db import models
from django.core.validators import MinLengthValidator
from async_property import async_property


class Author(models.Model):
    first_name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Author's first name"
    )

    last_name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text="Author's last name"
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        help_text="Author's date of birth"
    )

    nationality = models.CharField(
        max_length=100,
        blank=True,
        help_text="Author's nationality"
    )

    biography = models.TextField(
        blank=True,
        help_text="Brief biography of the author"
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
        help_text="Author's contact email"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(1)],
        help_text="Book title"
    )

    isbn = models.CharField(
        max_length=13,
        unique=True,
        help_text="International Standard Book Number (ISBN)"
    )

    publication_date = models.DateField(
        help_text="Date when the book was published"
    )

    publisher = models.CharField(
        max_length=200,
        blank=True,
        help_text="Publisher name"
    )

    pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of pages"
    )

    language = models.CharField(
        max_length=50,
        default='English',
        help_text="Language of the book"
    )

    description = models.TextField(
        blank=True,
        help_text="Brief description or synopsis of the book"
    )

    authors = models.ManyToManyField(
        Author,
        related_name='books',
        blank=False,
        help_text="Authors who wrote this book"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publication_date', 'title']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['publication_date']),
        ]

    def __str__(self):
        return self.title

    @property
    def author_names(self) -> str:
        return ", ".join([author.full_name for author in self.authors.all()])

    @async_property
    async def aauthor_names(self) -> str:
        authors = [author async for author in self.authors.all()]
        return ", ".join([author.full_name for author in authors])
