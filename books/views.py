import asyncio
from adrf import viewsets
from datetime import date, timedelta
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Avg, Max, Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Author, Book
from .serializers import (
    AuthorListSerializer,
    AuthorDetailSerializer,
    AuthorWriteSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookWriteSerializer,
)


async def _to_list(queryset):
    return [item async for item in queryset]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nationality', 'birth_date']
    search_fields = ['first_name', 'last_name', 'email', 'biography']
    ordering_fields = ['last_name', 'first_name', 'birth_date', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return AuthorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AuthorWriteSerializer
        return AuthorDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.prefetch_related('books')
        return queryset

    @extend_schema(
        summary="Get author statistics",
        description="Retrieve aggregated statistics using concurrent async queries to minimize response time"
    )

    @action(detail=False, methods=['get'])
    async def statistics(self, request):
        authors_with_book_count = Author.objects.annotate(
            book_count=Count('books')
        ).order_by('-book_count')

        authors_without_books = Author.objects.annotate(
            book_count=Count('books')
        ).filter(book_count=0)

        aggregated_stats, top_authors, authors_without_books_list, authors_without_books_count = await asyncio.gather(
            authors_with_book_count.aaggregate(
                total_authors=Count('id'),
                avg_books_per_author=Avg('book_count'),
                max_books=Max('book_count'),
                min_books=Min('book_count'),
            ),
            _to_list(authors_with_book_count[:5]),
            _to_list(authors_without_books[:10]),
            authors_without_books.acount()
        )

        return Response({
            'aggregated_statistics': {
                'total_authors': aggregated_stats['total_authors'],
                'average_books_per_author': round(aggregated_stats['avg_books_per_author'] or 0, 2),
                'max_books_by_single_author': aggregated_stats['max_books'] or 0,
                'min_books_by_single_author': aggregated_stats['min_books'] or 0,
            },

            'authors_without_books': {
                'count': authors_without_books_count,
                'authors': [
                    {
                        'id': author.id,
                        'name': author.full_name,
                        'nationality': author.nationality
                    }
                    for author in authors_without_books_list
                ]
            },
            'top_authors': [
                {
                    'id': author.id,
                    'name': author.full_name,
                    'nationality': author.nationality,
                    'book_count': author.book_count
                }
                for author in top_authors
            ]
        })

    @extend_schema(
        summary="List books by author",
        description="Retrieve all books written by a specific author"
    )
    @action(detail=True, methods=['get'])
    async def books(self, request, pk=None):
        author = await self.aget_object()
        books_qs = author.books.prefetch_related('authors')
        books = [book async for book in books_qs]

        serializer = BookListSerializer(books, many=True)
        return Response(await serializer.adata)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['language', 'publisher', 'publication_date']
    search_fields = ['title', 'isbn', 'description', 'publisher']
    ordering_fields = ['title', 'publication_date', 'pages', 'created_at']
    ordering = ['-publication_date', 'title']

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookWriteSerializer
        return BookDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.prefetch_related('authors')
        return queryset

    @extend_schema(
        summary="Get book statistics",
        description="Retrieve aggregated book statistics using concurrent async queries"
    )
    @action(detail=False, methods=['get'])
    async def statistics(self, request):
        books_with_author_count = Book.objects.annotate(
            author_count=Count('authors')
        ).order_by('-author_count')

        collaborative_books = books_with_author_count.filter(author_count__gt=1)

        books_by_language_qs = Book.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')

        book_stats, aggregated_stats, books_by_language, collaborative_books_list, collaborative_books_count = await asyncio.gather(
            books_with_author_count.aaggregate(
                avg_authors_per_book=Avg('author_count'),
            ),
            Book.objects.aaggregate(
                total_books=Count('id'),
                avg_pages=Avg('pages'),
                max_pages=Max('pages'),
                min_pages=Min('pages'),
                latest_publication=Max('publication_date'),
                earliest_publication=Min('publication_date'),
            ),
            _to_list(books_by_language_qs),
            _to_list(collaborative_books[:10]),
            collaborative_books.acount()
        )

        return Response({
            'aggregated_statistics': {
                'total_books': aggregated_stats['total_books'],
                'average_authors_per_book': round(book_stats['avg_authors_per_book'] or 0, 2),
                'average_pages': round(aggregated_stats['avg_pages'] or 0, 0),
                'max_pages': aggregated_stats['max_pages'] or 0,
                'min_pages': aggregated_stats['min_pages'] or 0,
                'latest_publication': aggregated_stats['latest_publication'],
                'earliest_publication': aggregated_stats['earliest_publication'],
            },

            'collaborative_books': {
                'count': collaborative_books_count,
                'books': [
                    {
                        'id': book.id,
                        'title': book.title,
                        'isbn': book.isbn,
                        'author_count': book.author_count
                    }
                    for book in collaborative_books_list
                ]
            },
            'books_by_language': books_by_language
        })

    @extend_schema(
        summary="List recent books",
        description="Retrieve books published in the last 5 years"
    )
    @action(detail=False, methods=['get'])
    async def recent(self, request):
        five_years_ago = date.today() - timedelta(days=5 * 365)

        recent_books = Book.objects.filter(
            publication_date__gte=five_years_ago
        ).annotate(
            author_count=Count('authors')
        ).order_by('-publication_date')

        recent_books_list = await _to_list(recent_books)
        serializer = BookListSerializer(recent_books_list, many=True)

        return Response({
            'count': len(recent_books_list),
            'books': await serializer.adata
        })
