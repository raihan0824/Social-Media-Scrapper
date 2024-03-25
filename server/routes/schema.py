from typing import Literal,Optional
from pydantic import BaseModel

class InputData(BaseModel):
    original_tweet_url: Optional[str] = "https://twitter.com/gibran_tweet/status/1660591660487831552"
    n_bots: Optional[int] = 10
    supporting_bots_ratio: Optional[float] = 0.8
    additional_context: Optional[str] = ''

