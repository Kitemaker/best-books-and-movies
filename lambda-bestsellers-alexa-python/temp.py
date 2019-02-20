from ask_sdk_core.skill_builder import SkillBuilder
import json

sb = SkillBuilder()
from ask_sdk_core.utils import is_request_type
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import  UserEvent
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand,
    AutoPageCommand, HighlightMode)
import requests
import  os
from ask_sdk_core.utils import is_intent_name


nyt_api_key = 'qWZ8p1pGBOto17VWY9ekXDaJQviMM2Gm'
query_lists = 'https://api.nytimes.com/svc/books/v3/lists/names.json'
qyery_bestseller = 'https://api.nytimes.com/svc/books/v3/lists.json'


@sb.request_handler(
    can_handle_func=lambda input :
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    speech_text = "Goodbye!"

    handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Hello World", speech_text))
    return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    #any cleanup logic goes here

    return handler_input.response_builder.response

@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Log the exception in CloudWatch Logs
    print(exception)

    speech = "Sorry, I didn't get it. Can you please say it again!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response

#handler = sb.lambda_handler()

#cat = prepare_list(load_apl_document("launch_bestseller_apl.json")['dataSources'])
# print('hello')
# cat = get_categories()
# cat1 = 'Trav'
# print(cat1 in cat)
# for i in cat:
#     if cat1 in i:
#         cat1 = i
# print(cat1 in cat)

query_critics_info = 'https://api.nytimes.com/svc/movies/v2/critics/all.json'
query_response = requests.get(query_lists, params={'api-key': nyt_api_key}, timeout=60).json()
print(query_response)

query_reviews = 'https://api.nytimes.com/svc/movies/v2/reviews/search.json'
res_reviews = requests.get(query_reviews, params={'api-key': nyt_api_key}, timeout=60).json()
print(res_reviews)

item_count = 10 if len(res_reviews['results']) >10 else len(res_reviews['results'])
import random
pick = list(range(item_count))
for x in range(item_count):
    print(pick)
    y = random.choice(pick)
    print(y)
    pick.pop(pick.index(y))
    print(res_reviews['results'][y]['display_title'])
