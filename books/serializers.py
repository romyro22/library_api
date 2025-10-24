from adrf import serializers as adrf_serializers
from adrf.fields import SerializerMethodField
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers as drf_serializers

from .models import Author, Book


class AuthorListSerializer(adrf_serializers.ModelSerializer):
    full_name = drf_serializers.ReadOnlyField()
    book_count = SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'full_name', 'nationality', 'book_count']

    @extend_schema_field(drf_serializers.IntegerField)
    async def get_book_count(self, obj) -> int:
        return await obj.books.acount()


class AuthorDetailSerializer(adrf_serializers.ModelSerializer):
    full_name = drf_serializers.ReadOnlyField()
    book_count = SerializerMethodField()

    books = SerializerMethodField()

    class Meta:
        model = Author

        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'birth_date',
            'nationality', 'biography', 'email', 'book_count', 'books',
            'created_at', 'updated_at'
        ]

        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(drf_serializers.IntegerField)
    async def get_book_count(self, obj) -> int:
        return await obj.books.acount()

    @extend_schema_field(drf_serializers.ListField(child=drf_serializers.DictField()))
    async def get_books(self, obj) -> list[dict[str, str | int]]:
        return [{'id': book.id, 'title': book.title, 'isbn': book.isbn} async for book in obj.books.all()]


class AuthorWriteSerializer(adrf_serializers.ModelSerializer):
    class Meta:
        model = Author

        fields = [
            'id', 'first_name', 'last_name', 'birth_date',
            'nationality', 'biography', 'email'
        ]


class BookListSerializer(adrf_serializers.ModelSerializer):
    author_count = SerializerMethodField()
    authors = AuthorListSerializer(many=True, read_only=True)

    class Meta:
        model = Book

        fields = [
            'id', 'title', 'isbn', 'publication_date', 'publisher',
            'language', 'author_count', 'authors'
        ]

    @extend_schema_field(drf_serializers.IntegerField)
    async def get_author_count(self, obj) -> int:
        return await obj.authors.acount()


class BookDetailSerializer(adrf_serializers.ModelSerializer):
    author_count = SerializerMethodField()
    author_names = SerializerMethodField()
    authors = AuthorListSerializer(many=True, read_only=True)

    class Meta:
        model = Book

        fields = [
            'id', 'title', 'isbn', 'publication_date', 'publisher',
            'pages', 'language', 'description', 'author_count',
            'author_names', 'authors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    @extend_schema_field(drf_serializers.IntegerField)
    async def get_author_count(self, obj) -> int:
        return await obj.authors.acount()

    @extend_schema_field(drf_serializers.CharField)
    async def get_author_names(self, obj) -> str:
        return await obj.aauthor_names


class BookWriteSerializer(adrf_serializers.ModelSerializer):
    class Meta:
        model = Book

        fields = [
            'id', 'title', 'isbn', 'publication_date', 'publisher',
            'pages', 'language', 'description', 'authors'
        ]

        extra_kwargs = {
            'authors': {'allow_empty': False, 'required': True}
        }

    def validate_isbn(self, value):
        isbn = value.replace('-', '').replace(' ', '')
        if not isbn.isdigit():
            raise drf_serializers.ValidationError("ISBN must contain only digits (hyphens and spaces are allowed).")
        if len(isbn) not in [10, 13]:
            raise drf_serializers.ValidationError("ISBN must be either 10 or 13 digits long.")
        return value

    def validate(self, attrs):
        authors = attrs.get('authors', [])

        if not authors or len(authors) == 0:
            raise drf_serializers.ValidationError({"authors": "A book must have at least one author."})
        return attrs
