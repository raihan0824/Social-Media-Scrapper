import uuid
from datetime import datetime

def convert_post_to_conversation(post,post_id):
    current_time = datetime.now()
    convo_id=str(uuid.uuid4())
    return{ 
        "id":convo_id, 
        "post_id":post_id,
        "num_of_bot":post["n_bots"],
        "context":post["additional_context"],
        "slider_ratio":post["supporting_bots_ratio"],
        "scheduled_at":None,
        "created_at":current_time,
        "updated_at":current_time,
    }

def convert_post_to_replies(post,conversation_id):
    current_time = datetime.now()
    return{
        "id":str(uuid.uuid4()),
        "task_id":str(uuid.uuid4()),
        "post_id":post["id"], 
        "conversation_id":conversation_id, 
        "bot_id":post["bot_id"],
        "reply_id":None, 
        "content":post["content"], 
        "scheduled_at":None,
        "created_at":current_time,
        "updated_at":current_time
    }

def convert_posts_format(data,url):
    current_time = datetime.now()
    metadata={}
    metadata["id"]=str(uuid.uuid4())
    metadata["task_id"]=None
    metadata["url"]=url
    metadata["username"]=data['user']['screen_name']
    metadata["content"]=data['text']
    metadata["created_at"]=current_time
    metadata["updated_at"]=current_time
    metadata["scheduled_at"]=None
    metadata["post_created_at"]=data['created_at']

    metadata["pro_1_score"]=0
    metadata["con_1_score"]=0
    metadata["pro_2_score"]=0
    metadata["con_2_score"]=0
    metadata["pro_3_score"]=0
    metadata["con_3_score"]=0
    metadata["topic"]=None
    metadata["subtopic"]=None

    metadata["bot_id"] = None
    return metadata


