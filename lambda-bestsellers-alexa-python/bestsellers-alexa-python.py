from ask_sdk_core.skill_builder import SkillBuilder
import json
sb = SkillBuilder()
from ask_sdk_core.utils import is_request_type
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.handler_input import HandlerInput
import copy
from ask_sdk_model.dialog.elicit_slot_directive import ElicitSlotDirective
from ask_sdk_model.dialog.delegate_directive import DelegateDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import UserEvent
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand,
    AutoPageCommand, HighlightMode)
import requests
import os
from ask_sdk_core.utils import is_intent_name

default_image = "https://s3.amazonaws.com/aws-apl-contest/bestsellers/categories/books.jpg"
nyt_api_key = os.environ['NYT_API_KEY']
query_lists = 'https://api.nytimes.com/svc/books/v3/lists/names.json'
qyery_bestseller = 'https://api.nytimes.com/svc/books/v3/lists.json'
query_moview_reviews = 'https://api.nytimes.com/svc/movies/v2/reviews/search.json'
list_item_template = str()
book_item_template = str()
cat_images = str()
TAG = 'bestsellers-alexa-python'
with open('category_item_template.json') as f:
    list_item_template = json.load(f)

with open('category_image_map.json') as f:
    cat_images = json.load(f)

with open('book_item_template.json') as f:
    book_item_template = json.load(f)

def load_apl_document(file_path):
    # type: (str) -> Dict[str, Any]
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)


def get_categories():
    categories = list()
    query_response = requests.get(query_lists, params={'api-key': nyt_api_key}, timeout=60).json()
    if query_response['status'] == 'OK':
        for item in query_response['results']:
            categories.append(item['list_name'])
        return categories
    else:
        print('Some error in getting categories from API status = ' +  query_response['status'])
        return None

def prepare_category_list(data_source):
    with open('category_names.json') as f:
        major_category_names = json.load(f)['major_categories']
        # get categories from API
        cat_list = get_categories()
        # use 20 major categories from static list find if any one is not API list then replace it
        for i in range(len(major_category_names)):
            name_without_newline  = major_category_names[i].replace('\n','')
            if name_without_newline not in cat_list:
                for j in range(len(cat_list)):
                    if cat_list[j] not in major_category_names:
                        major_category_names[i] = cat_list[j]
                        break


    listTemplate1ListData = data_source['listTemplate1ListData']

    if len(major_category_names) > 0:
        listTemplate1ListData['totalNumberOfItems'] = len(major_category_names)

        for i in range(len(major_category_names)):
            item = copy.deepcopy(list_item_template)
            item['listItemIdentifier'] = major_category_names[i]
            item['ordinalNumber'] = i + 1
            item['textContent']['primaryText']['text'] = major_category_names[i]
            # secondaryText shall be used to display
            split_major_name = major_category_names[i].split(' ')
            if len(split_major_name)> 2:
                split_major_name.insert(2,'\n')

            item['textContent']['secondaryText']['text'] = "  ".join(split_major_name)


            #if cat_images.get(major_category_names[i]) is not None:
                #print(cat_images[major_category_names[i]])
               # item['image']['sources'][0]["url"] = cat_images[major_category_names[i]] # TBD
               # item['image']['sources'][1]["url"] = cat_images[major_category_names[i]]# TBD
            #else:
                #item['image']['sources'][0]["url"] =  default_image
                #item['image']['sources'][1]["url"] = default_image
            item['token'] = major_category_names[i]
            listTemplate1ListData['listPage']['listItems'].append(copy.deepcopy(item))
            #if i == 19:
                #break


    data_source['listTemplate1ListData'] = listTemplate1ListData
    return data_source

def prepare_book_list(data_source, book_list, category):
    listTemplate1ListData = data_source['listTemplate1ListData']
    data_source['listTemplate1Metadata']['title'] = "Bestsellers for " + category

    if len(book_list) > 0:
        listTemplate1ListData['totalNumberOfItems'] = len(book_list)

        for i in range(len(book_list)):
            item = copy.deepcopy(book_item_template)
            item['listItemIdentifier'] = book_list[i]['title']
            item['ordinalNumber'] = book_list[i]['rank']
            item['textContent']['primaryText']['text'] = book_list[i]['title']
            #item['textContent']['secondaryText']['text'] = book_list[i]['description']
            item['textContent']['secondaryText']['text'] = ""
            item['textContent']['tertiaryText']['text'] =  ""

            item['token'] = book_list[i]['title']
            listTemplate1ListData['listPage']['listItems'].append(copy.deepcopy(item))

    data_source['listTemplate1ListData'] = listTemplate1ListData
    return data_source

def get_bestsellers_list(category):
    bestsellers = list()
    book = dict()
    response = requests.get(qyery_bestseller, params={'api-key': nyt_api_key, 'list': category}, timeout=60).json()
    if response['status'] == 'OK' and len(response['results']) > 0:
        for i in range(len(response['results'])):
            try:
                book['rank'] = response['results'][i]['rank']
                book['amazon_product_url'] = response['results'][i]['amazon_product_url']
                book['primary_isbn10'] = response['results'][i]['book_details'][0]['primary_isbn10']
                book['title'] = response['results'][i]['book_details'][0]['title']
                book['description'] = response['results'][i]['book_details'][0]['description']
                bestsellers.append(copy.deepcopy(book))
            except:
                print(TAG + 'Error while fetching book details ' + str(i))
    return bestsellers


def fill_single_book_template(bestsellers, rank, speech_text, handler_input, category):
    print("Executing method fill_single_book_template")
    for i in range(len(bestsellers)):
        print('rank = {0}'.format(bestsellers[i]['rank']))
        print(str(bestsellers[i]['rank']) == str(rank))
        if str(bestsellers[i]['rank']) == str(rank):
            speech_text = speech_text + " On rank {0},  book is  {1}. {2}".format(bestsellers[i]['rank'],
                                                                                  bestsellers[i]['title'],
                                                                                  bestsellers[i]['description'])
            books_datasource = load_apl_document("apl_single_book.json")['dataSources']
            books_datasource['bodyTemplate2Data']['title'] = "Category: " + category
            books_datasource['bodyTemplate2Data']['textContent']['title']['text'] = bestsellers[i]['title']
            books_datasource['bodyTemplate2Data']['textContent']['subtitle']['text'] = 'Rank: ' + str(
                bestsellers[i]['rank'])
            books_datasource['bodyTemplate2Data']['textContent']['isbn']['text'] = "ISBN10:" + str(
                bestsellers[i]['primary_isbn10'])
            books_datasource['bodyTemplate2Data']['textContent']['primaryText']['text'] = bestsellers[i]['description']
            print(TAG + speech_text)
            handler_input.response_builder.speak(speech_text).set_should_end_session(
                False).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_single_book.json")['document'],
                    datasources=books_datasource
                )
            )
            break


def handle_get_book_list(handler_input, category, rank=None):
    bestsellers = get_bestsellers_list(category)
    handler_input.attributes_manager.session_attributes['category'] = category
    handler_input.attributes_manager.session_attributes['book_list'] = bestsellers
    print(bestsellers)
    speech_text = "Sorry could not find bestsellers list. Please try again"
    if bestsellers is not None and len(bestsellers)>0:
        if rank is None:
            speech_text = "For category {0}".format(category)
            for i in range(len(bestsellers)):
                speech_text = speech_text + " On rank {0},  book is  {1}. {2}".format(bestsellers[i]['rank'],
                                                                                          bestsellers[i]['title'],
                                                                                          bestsellers[i]['description'])

            books_datasource = prepare_book_list(load_apl_document("books_list_apl.json")['dataSources'],
                                                     bestsellers, category)
            print(TAG + "Book List is ")
            handler_input.response_builder.speak(speech_text).set_should_end_session(
                False).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("books_list_apl.json")['document'],
                    datasources=books_datasource
                    )
                )
        else:
            speech_text = "For category {0}".format(category)
            fill_single_book_template(bestsellers, rank, speech_text, handler_input, category)

    else:
        handler_input.response_builder.speak(speech_text).set_should_end_session(True)

def navigate_home_handler(handler_input):
    speech_text = "To get the New York Times Best sellers list you can say find books list for sports!"
    print('request = {0}'.format(handler_input.request_envelope.request))
    handler_input.response_builder.speak(speech_text).set_should_end_session(
         False).add_directive(
        RenderDocumentDirective(
                token="listToken",
                document=load_apl_document("apl_launch_bestseller.json")['document'],
                datasources=load_apl_document("apl_launch_bestseller.json")['dataSources']
            )
    )

@sb.request_handler(can_handle_func=is_intent_name("GetBestSellerIntent"))
def get_bestsellers_intent_handler(handler_input):

    slots = handler_input.request_envelope.request.intent.slots
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent

    if 'category' in slots:
        print('slot category = {0}'.format(slots['category'].value))
        category_value = slots['category'].value
    else:
        category_value = None

    if 'rank' in slots:
        print('slot rank = {0}'.format(slots['rank'].value))
        rank_value = slots['rank'].value
    else:
        rank_value = None

    speech_text = ""

    if dialogstate.value != "COMPLETED" and category_value is None:
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))
        return handler_input.response_builder.response

    else:
        # if no exact match for category then find nearest match
        cat_list = get_categories()
        if category_value not in cat_list:
            for cat in cat_list:
                if category_value in cat:
                    category_value = cat

        print(str.format("Getting books for category = {0} and rank = {1}", category_value, rank_value))
        if rank_value is None:
            handle_get_book_list(handler_input, category_value, rank=None)
        else:
            handle_get_book_list(handler_input, category_value, rank=rank_value)
    return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    speech_text = "Welcome to Best Media Info, to get the New York Times Best sellers list you can say find books list for sports!"
    print('request = {0}'.format(handler_input.request_envelope.request))
    handler_input.response_builder.speak(speech_text).set_should_end_session(
         False).add_directive(
        RenderDocumentDirective(
                token="listToken",
                document=load_apl_document("apl_launch_bestseller.json")['document'],
                datasources=load_apl_document("apl_launch_bestseller.json")['dataSources']
            )
    )
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input :
        is_intent_name("AMAZON.NavigateHomeIntent")(input) or
        is_intent_name("HomeIntent")(input))
def launch_request_handler(handler_input):
    navigate_home_handler(handler_input)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("Alexa.Presentation.APL.UserEvent"))
def alexa_user_event_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch

    print('AWS: alexa_user_event_request_handler')
    print('request = {0}'.format(handler_input.request_envelope.request))
    print('object_type = {0}'.format(handler_input.request_envelope.request.object_type))
    arguments = handler_input.request_envelope.request.arguments
    request_type = handler_input.request_envelope.request.object_type

    if len(arguments) >= 3:
        item_selected = arguments[0]
        item_ordinal =  arguments[1]
        item_title = arguments[2]

    if item_selected == "LogoItem":
        navigate_home_handler(handler_input)
        return handler_input.response_builder.response

    if item_selected == 'LaunchTemplateItem':
        if item_title == 'Books':
            # Launch Book Category
            speech_text = "Following are the bestseller books categories. Please select one category"
            new_datasource = prepare_category_list(load_apl_document("apl_books_categories.json")['dataSources'])
            handler_input.response_builder.speak(speech_text).set_should_end_session(
                False).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_books_categories.json")['document'],
                    datasources=new_datasource
                )
            )

        if item_title == 'Movies':
            # Launch Book Category
            speech_text = "Following are brief movie reviews"
            res_reviews = requests.get(query_moview_reviews, params={'api-key': nyt_api_key}, timeout=60).json()
            if str.lower(res_reviews['status']) == 'ok':
                fill_movie_list(handler_input, res_reviews)
            else:
                speech_text = "Sorry could find movie reviews at this time. Please try again"
                handler_input.response_builder.speak(speech_text).ask(speech_text)


        if item_title == 'Top Stories':
            # Launch Book Category
            speech_text = "Following are the Top Stories today"
            new_datasource = prepare_category_list(load_apl_document("apl_books_categories.json")['dataSources'])
            handler_input.response_builder.speak(speech_text).set_should_end_session(
                False).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_books_categories.json")['document'],
                    datasources=new_datasource
                )
            )

    elif item_selected == "BookCategories":
        handle_get_book_list(handler_input, item_title, rank=None)

    elif item_selected == "BookItem":
        if 'category' in handler_input.attributes_manager.session_attributes:
            category = handler_input.attributes_manager.session_attributes['category']
        if 'book_list' in handler_input.attributes_manager.session_attributes:
            book_list = handler_input.attributes_manager.session_attributes['book_list']
            print('book list for category {0} is {1}'.format(category, book_list))
        fill_single_book_template(book_list, item_ordinal, "", handler_input, category)

    elif item_selected == 'MovieItem':
        if 'movie_review_data' in handler_input.attributes_manager.session_attributes:
            movie_review_data = handler_input.attributes_manager.session_attributes['movie_review_data']
            movie_item  = movie_review_data[item_ordinal -1]
            print('loading movie data {0}'.format(movie_item))
            movie_datasource = load_apl_document("apl_single_movie.json")['dataSources']
            movie_datasource['bodyTemplate2Data']['title'] = 'NYT Movie Review'
            movie_datasource['bodyTemplate2Data']['textContent']['title']['text'] = movie_item['display_title']
            movie_datasource['bodyTemplate2Data']['textContent']['subtitle']['text'] = 'Critics Pick: ' + str(
                movie_item['critics_pick'])
            movie_datasource['bodyTemplate2Data']['textContent']['isbn']['text'] = "Headline: " + movie_item['headline']
            summery = 'Summery: {0} \nLink: {1} \nOpening Date: {2}'.format(
                movie_item['summary_short'], movie_item['link']['url'], movie_item['opening_date'])

            movie_datasource['bodyTemplate2Data']['textContent']['primaryText']['text'] = summery
            try:
                movie_datasource['bodyTemplate2Data']['image']['sources'][0]['url'] = movie_item['multimedia']['src']
                movie_datasource['bodyTemplate2Data']['image']['sources'][1]['url'] = movie_item['multimedia']['src']
            except:
                print('error while loading image')

            handler_input.response_builder.speak("").set_should_end_session(
                False).add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_single_movie.json")['document'],
                    datasources=movie_datasource
                )
            )



    return handler_input.response_builder.response



@sb.request_handler(can_handle_func=is_intent_name("GetBookCategoriesIntent"))
def get_categories_handler(handler_input):

    cat_list = get_categories()
    if cat_list is not None:
        speech_text = "Here are the book categories, {0}".format(", ".join(cat_list))
        new_datasource = prepare_category_list(load_apl_document("apl_books_categories.json")['dataSources'])
        handler_input.response_builder.speak(speech_text).set_should_end_session(
            False).add_directive(
            RenderDocumentDirective(
                token="listToken",
                document=load_apl_document("apl_books_categories.json")['document'],
                datasources=new_datasource
            )
        )
    else:
        speech_text = "Sorry could not get the data you are looking for. Please try again"
        handler_input.response_builder.speak(speech_text).ask(speech_text)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    speech_text = "To find New york times bestseller Books list you can say find books for sports" +\
                  " and if you want to know the categories you can say get book categories"

    handler_input.response_builder.speak(speech_text).ask(speech_text).add_directive(
            RenderDocumentDirective(
                token="pagerToken",
                document=load_apl_document("apl_launch_bestseller.json")['document'],
                datasources=load_apl_document("apl_launch_bestseller.json")['dataSources']
            )
    )
    return handler_input.response_builder.response


#***************************Movie Review *******************************************************


def fill_movie_list(handler_input, res_reviews):
    review_text_list = list()
    # will pick any 5 moview review randomly
    data_source = load_apl_document('apl_movie_list.json')['dataSources']
    data_movie_list = data_source['listTemplate1ListData']['listPage']['listItems']
    item_count = 5 if len(res_reviews['results']) > 5 else len(res_reviews['results'])
    import random
    pick = list(range(len(res_reviews['results'])))
    movie_data_attr = list()
    movie_index_selected = list()
    for i in range(item_count):
        movie_index = random.choice(pick)
        movie_index_selected.append(movie_index)
        print(movie_index)
        pick.pop(pick.index(movie_index))
        movie_item = res_reviews['results'][movie_index]
        review_text = 'Movie name is {0} critics pick is {1}, movie opening date is {2} and summery is {3}'.format(
            movie_item['display_title'], movie_item['critics_pick'], movie_item['opening_date'],
            movie_item['summary_short']
        )
        review_text_list.append(review_text)

        # fill APL Template
        print(review_text)
        # only five elements
        if i < 5:
            data_movie_list[i]['textContent']['primaryText']['text'] = movie_item['display_title']
            data_movie_list[i]['textContent']['secondaryText']['text'] = movie_item['headline']
            # for session attribute
            movie_data_attr.append(movie_item)

    handler_input.attributes_manager.session_attributes['movie_review_data'] = movie_data_attr
    handler_input.attributes_manager.session_attributes['movie_index_selected'] = movie_index_selected
    data_source['listTemplate1ListData']['listPage']['listItems'] = data_movie_list
    speech_text = 'Movie reviews from New York Times are as following {0} For more details you can visit the website of new york times'.format(
        ", ".join(review_text_list))

    handler_input.response_builder.speak(speech_text).ask(speech_text).set_should_end_session(
        False).add_directive(
        RenderDocumentDirective(
            token="listToken",
            document=load_apl_document('apl_movie_list.json')['document'],
            datasources=data_source
        )
    )


@sb.request_handler(can_handle_func=is_intent_name("MovieReviewIntent"))
def get_movie_review_intent_handler(handler_input):
    speech_text = ""
    res_reviews = requests.get(query_moview_reviews, params={'api-key': nyt_api_key}, timeout=60).json()

    if str.lower(res_reviews['status']) == 'ok':
        fill_movie_list(handler_input, res_reviews)
    else:
        speech_text = "Sorry could find movie reviews at this time. Please try again"
        handler_input.response_builder.speak(speech_text).ask(speech_text)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input :
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    speech_text = "Goodbye!"

    handler_input.response_builder.speak(speech_text)
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

handler = sb.lambda_handler()

