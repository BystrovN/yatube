from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator_form

CACHE_DURATION: int = 20


def index(request):
    """Главная страница."""
    posts = Post.objects.select_related('group', 'author')
    search_query = request.GET.get('search', '')
    if search_query:
        posts = Post.objects.select_related('group', 'author').filter(
            Q(text__icontains=search_query)
            | Q(group__slug__icontains=search_query)
            | Q(author__username__icontains=search_query)
            | Q(author__first_name__icontains=search_query)
            | Q(author__last_name__icontains=search_query)
            | Q(pub_date__icontains=search_query)
            | Q(comments__text__icontains=search_query)
        )
    page_obj = paginator_form(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Все посты определенной группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = paginator_form(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница пользователя."""
    users = get_object_or_404(User, username=username)
    posts = users.posts.select_related('group')
    page_obj = paginator_form(request, posts)
    following = request.user.is_authenticated and request.user.follower.filter(
        author=users
    ).exists()
    context = {
        'users': users,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница определенного поста."""
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """
    Создание нового поста.
    Только для зарегистрированных пользователей.
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(
            'posts:profile',
            username=request.user.username
        )
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """
    Изменение существующего поста.
    Только для зарегистрированных пользователей.
    Изменение доступно только автору поста.
    """
    post = get_object_or_404(Post, id=post_id)
    if post_id and post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """
    Комментирование поста.
    Только для зарегистрированных пользователей.
    """
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Посты авторов из подписок пользователя."""
    user = get_object_or_404(User, username=request.user.username)
    posts = Post.objects.select_related('group', 'author').filter(
        author__in=user.follower.values('author')
    )
    page_obj = paginator_form(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    author = get_object_or_404(User, username=username)
    if request.user.username != username:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    follow_qs = Follow.objects.filter(user=request.user, author=author)
    if follow_qs.exists():
        follow_qs.delete()
    return redirect('posts:profile', username=username)


@login_required
def post_delete(request, post_id):
    """Удаление поста. Только для автора."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    post.delete()
    cache.clear()
    return redirect('posts:index')


@login_required
def user_delete(request, username):
    """Удаление пользователя. Только для самого пользователя."""
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return redirect('posts:profile', username=username)
    user.delete()
    cache.clear()
    return redirect('posts:index')
