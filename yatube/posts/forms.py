from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    """Форма создания/изменения поста."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(ModelForm):
    """Форма добавления комментария к посту."""
    class Meta:
        model = Comment
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['cols'] = 10
        self.fields['text'].widget.attrs['rows'] = 5
