from datetime import datetime
from typing import List

from sqlalchemy import func

from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from app.models import Posts, VotesModel
from app.oauth2 import get_current_user
from app.schema import (PostBaseSchema, PostErrorSchema, PostResponseSchema, PostVoteSchema,
                    PostVoteResponseSchema, PostSchema, UserBaseSchema, PostOutputSchema)
from sqlalchemy.orm import Session

router = APIRouter(
    tags=['Posts']
)


@router.get('/', status_code=status.HTTP_200_OK, response_model=PostVoteResponseSchema)
def get_posts(
    db: Session = Depends(get_db),
    get_current_user: UserBaseSchema = Depends(get_current_user),
    limit: int = 10,
    page: int = 1,
    title: str = '',
    content: str = ''
):
    posts_query = db.query(
        Posts,
        func.count(VotesModel.post_id).label('votes')
    ).join(
        VotesModel,
        VotesModel.post_id == Posts.id,
        isouter=True
    ).group_by(
        Posts.id
    ).filter(
        Posts.is_published == True,
        Posts.is_deleted == False,
        Posts.title.contains(title),
        Posts.content.contains(content),
    ).limit(limit).offset(limit*(page-1)).all()

    posts_list: List[PostVoteSchema] = []
    for post in posts_query:
        posts_list.append(PostVoteSchema(**post))
    response = PostResponseSchema(
        message="Posts fetched successfully",
        data=posts_list
    )
    return response


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=PostVoteResponseSchema)
def get_posts_by_id(id: int, db: Session = Depends(get_db), get_current_user: UserBaseSchema = Depends(get_current_user)):
    post = db.query(
        Posts,
        func.count(VotesModel.post_id).label('votes')
    ).filter(
        Posts.id == id,
        Posts.is_published == True,
        Posts.is_deleted == False
    ).join(
        VotesModel,
        VotesModel.post_id == Posts.id,
        isouter=True
    ).group_by(Posts.id).first()

    if not post:
        response = PostErrorSchema(
            message="Requested post not found",
            error=post
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=response.dict()
        )

    response = PostVoteResponseSchema(
        message="Post fetched successfully",
        data=PostVoteSchema(**post)
    )
    return response


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=PostResponseSchema)
def create_post(payload: PostBaseSchema, db: Session = Depends(get_db), get_current_user: UserBaseSchema = Depends(get_current_user)):
    new_post = Posts(owner_id=get_current_user.id, **payload.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    response = PostResponseSchema(
        message="Post created successfully",
        data=PostSchema(**jsonable_encoder(new_post))
    )
    return response


@router.put('/{id}', status_code=status.HTTP_200_OK, response_model=PostResponseSchema)
def update_post(id: int, payload: PostBaseSchema, db: Session = Depends(get_db), get_current_user: UserBaseSchema = Depends(get_current_user)):
    update_query = db.query(
        Posts
    ).filter(
        Posts.id == id,
        Posts.is_published == True,
        Posts.is_deleted == False
    )
    post = update_query.first()

    if post == None:
        response = PostErrorSchema(
            message="Requested post not found",
            error=None
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=response.dict()
        )
    if post.owner_id != get_current_user.id:
        response = PostErrorSchema(
            message="Not authorized to perform this action",
            error=None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=response.dict()
        )

    try:
        post.title = payload.title
        post.content = payload.content
        post.is_published = payload.is_published
        data = PostSchema(**post.__dict__)
        update_query.update({
            Posts.updated_at: datetime.now().astimezone(),
            **payload.dict()}, synchronize_session=False
        )
        db.commit()
        response = PostResponseSchema(
            message="Post updated successfully",
            data=PostSchema(**jsonable_encoder(data))
        )
        return response
    except Exception as error:
        print("Error==> ", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=jsonable_encoder(error))


@router.delete('/{id}', status_code=status.HTTP_200_OK, response_model=PostResponseSchema)
def delete_post(id: int, db: Session = Depends(get_db), get_current_user: UserBaseSchema = Depends(get_current_user)):
    deleted_post = db.query(
        Posts
    ).filter(
        Posts.id == id,
        Posts.is_published == True,
        Posts.is_deleted == False
    )
    if deleted_post.first() == None:
        response = PostErrorSchema(
            message="Requested post not found",
            error=None
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=response.dict()
        )
    if deleted_post.first().owner_id != get_current_user.id:
        response = PostErrorSchema(
            message="Not authorized to perform this action",
            error=None
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=response.dict()
        )
    deleted_post.update({Posts.is_deleted: True},
                        synchronize_session=False)
    db.commit()

    response = PostResponseSchema(
        message="Post deleted successfully",
        data=None
    )
    return response
