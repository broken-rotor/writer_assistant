# Endpoints RequestContext integration


| Endpoint                            | RqCtx    | Fields        | Works
| ----------------------------------- | -------- | ------------- | ---------------------------------------- |
| character_feedback_router           |  Yes     |  No           |  Always uses characters[0]               |
| generate_chapter_router             |  Yes     |  Yes          |  ?                                       |
| modify_chapter_router               |  Yes     |  Yes          |  ?                                       |
| editor_review_router                |  Yes     |  Yes          |  ? using editor prompt?                  |
| flesh_out_router                    |  Yes     |  Too many     |  ?                                       |
| generate_character_details_router   |  ?       |               |                                          |
| generate_chapter_outlines_router    |  Yes     |  No*          | Probably already in the requestcontext   |
| regenerate_bio.router               |  Yes     |  Yes          | ?                                        |
| llm_chat.router                     |  Yes     |  Yes?         | ?                                        |
