from django.contrib import admin
from .models import Author, Book



class BookInline(admin.TabularInline):
    model = Book.authors.through
    extra = 1
    verbose_name = "Book"
    verbose_name_plural = "Books"

class AuthorInline(admin.TabularInline):
    model = Book.authors.through
    extra = 1
    verbose_name = "Author"
    verbose_name_plural = "Authors"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'nationality', 'birth_date', 'email', 'book_count']
    list_filter = ['nationality', 'birth_date']
    search_fields = ['first_name', 'last_name', 'email', 'nationality']
    ordering = ['last_name', 'first_name']
    date_hierarchy = 'birth_date'

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'birth_date', 'nationality')
        }),
        ('Contact & Biography', {
            'fields': ('email', 'biography')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookInline]

    def book_count(self, obj):
        return obj.books.count()

    book_count.short_description = 'Books'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'publication_date', 'publisher', 'pages', 'language', 'author_count']
    list_filter = ['publication_date', 'language', 'publisher']
    search_fields = ['title', 'isbn', 'publisher', 'description']
    ordering = ['-publication_date', 'title']
    date_hierarchy = 'publication_date'
    filter_horizontal = ['authors']

    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'isbn', 'publication_date', 'publisher', 'pages', 'language')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Authors', {
            'fields': ('authors',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def author_count(self, obj):
        return obj.authors.count()

    author_count.short_description = 'Authors'


admin.site.site_header = "Books & Authors Administration"
admin.site.site_title = "Books Admin"
admin.site.index_title = "Welcome to Books & Authors Management"
