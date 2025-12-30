from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from django.contrib.auth.decorators import login_required

@login_required
def registrar_blog(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        
        nuevo_post = Post(
            titulo=titulo,
            contenido=contenido,
            autor=request.user,
            publicado=False
        )
        nuevo_post.save()
        
        try:
            return redirect('blog:listar_publicaciones')
        except:
            return redirect('listar_publicaciones')
        
    return render(request, 'blog/registrar.html')


def listar_publicaciones(request):
    if request.user.is_authenticated:
        # Si está logueado, ve sus propios posts (borradores + publicados)
        posts = Post.objects.filter(autor=request.user).order_by('-fecha_publicacion')
    else:
        # Si NO está logueado, solo ve los que ya están publicados
        posts = Post.objects.filter(publicado=True).order_by('-fecha_publicacion')
    
    return render(request, 'blog/publicar.html', {'posts': posts})

@login_required
def eliminar_blog(request, post_id):
    post = get_object_or_404(Post, id=post_id, autor=request.user)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:listar_publicaciones')
        
    return render(request, 'blog/eliminar.html', {'post': post})