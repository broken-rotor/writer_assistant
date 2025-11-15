# Endpoints RequestContext integration


| Endpoint                            | RqCtx    | Fields        | Works
| ----------------------------------- | -------- | ------------- | ---------------------------------------- |
| /character-feedback                 |  Yes     |  No           | Always uses characters[0]                |
| /editor-review                      |  Yes     |  Yes          | ? using editor prompt?                   |
| /flesh-out                          |  Yes     |  Too many     | Migrated                                 |
| /generate-chapter                   |  Yes     |  Yes          | ?                                        |
| /generate-chapter-outlines          |  Yes     |  No           | Migrated                                 |
| /generate-character-details         |  Yes     |  Too many     | Extra characters field                   |
| /chat/llm                           |  Yes     |  Yes?         | ?                                        |
| /modify-chapter                     |  Yes     |  Yes          | ?                                        |
| /rater-feedback                     |  Yes     |  Yes          | ?                                        |
| /regenerate-bio                     |  Yes     |  Yes          | ?                                        |
