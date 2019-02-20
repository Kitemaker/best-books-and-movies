from ask_sdk_core.skill_builder import SkillBuilder
import json

from ask_sdk_core.utils import is_request_type
from ask_sdk.standard import StandardSkillBuilder
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

sb = StandardSkillBuilder(table_name='Best_Media_Info',auto_create_table=False)


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


def is_apl_supported(handler_input):

    if  handler_input.request_envelope.context.system.device.supported_interfaces.alexa_presentation_apl is None:
        return False
    else:
        return True


def get_categories():
    print(' message from function = {0}'.format('get_categories'))
    categories = list()
    try:
        query_response = requests.get(query_lists, params={'api-key': nyt_api_key}, timeout=60).json()
        if query_response['status'] == 'OK':
            for item in query_response['results']:
                categories.append(item['list_name'])
            return categories
        else:
            print('Some error in getting categories from API status = ' +  query_response['status'])
            return None
    except Exception as exc:
        print("Error sourc = get_categories, Error = {0}".format(exc.args[0]))
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
    print(' message from function = {0}'.format('fill_single_book_template'))
    ask_text = ' To know more about books, you can say find books or say stop.'
    for i in range(len(bestsellers)):
        print('rank = {0}'.format(bestsellers[i]['rank']))
        print(str(bestsellers[i]['rank']) == str(rank))
        if str(bestsellers[i]['rank']) == str(rank):
            speech_text = speech_text + " On rank {0},  book is  {1}. {2}".format(bestsellers[i]['rank'],
                                                                                  bestsellers[i]['title'],
                                                                                  bestsellers[i]['description'])
            books_datasource = load_apl_document("apl_single_book.json")['datasources']
            books_datasource['bodyTemplate2Data']['title'] = "Category: " + category
            books_datasource['bodyTemplate2Data']['textContent']['title']['text'] = bestsellers[i]['title']
            books_datasource['bodyTemplate2Data']['textContent']['subtitle']['text'] = 'Rank: ' + str(
                bestsellers[i]['rank'])
            books_datasource['bodyTemplate2Data']['textContent']['isbn']['text'] = "ISBN10:" + str(
                bestsellers[i]['primary_isbn10'])
            books_datasource['bodyTemplate2Data']['textContent']['primaryText']['text'] = bestsellers[i]['description']
            
            if is_apl_supported(handler_input):
                handler_input.response_builder.speak(speech_text + ask_text).ask(ask_text).set_should_end_session(False).add_directive(
                    RenderDocumentDirective(
                        token="listToken",
                        document=load_apl_document("apl_single_book.json")['document'],
                        datasources=books_datasource
                    )
                )
            else:
                handler_input.response_builder.speak(speech_text).set_should_end_session(False)

            break


def handle_get_book_list(handler_input, category, rank=None):
    print(' message from function = {0}'.format('handle_get_book_list'))
    bestsellers = get_bestsellers_list(category)
    handler_input.attributes_manager.session_attributes['category'] = category
    handler_input.attributes_manager.session_attributes['book_list'] = bestsellers
    ask_text = ' To know more about books, you can say find books or say stop.'
   
    speech_text = "Sorry could not find bestsellers list. Please try again"
    if bestsellers is not None and len(bestsellers)>0:
        if rank is None:
            speech_text = "For category {0} bestselling books are. ".format(category)
            for i in range(len(bestsellers)):
                speech_text = speech_text + " On rank {0},  book name is  {1}. {2}".format(bestsellers[i]['rank'],
                                                                                          bestsellers[i]['title'],
                                                                                          bestsellers[i]['description'])

            books_datasource = prepare_book_list(load_apl_document("books_list_apl.json")['datasources'],
                                                     bestsellers, category)
            speech_text = speech_text + ask_text
            
            handler_input.response_builder.speak(speech_text).ask(ask_text).set_should_end_session(False)
            if is_apl_supported(handler_input):
                handler_input.response_builder.add_directive(
                    RenderDocumentDirective(
                        token="listToken",
                        document=load_apl_document("books_list_apl.json")['document'],
                        datasources=books_datasource
                        )
                    )
        else:
            speech_text = "For category {0} ".format(category)
            fill_single_book_template(bestsellers, rank, speech_text, handler_input, category)

    else:
        handler_input.response_builder.speak(speech_text).set_should_end_session(False)


def navigate_home_handler(handler_input, speech_text, ask_text=""):
    
    handler_input.attributes_manager.session_attributes['current_movie_index'] = 0
    handler_input.attributes_manager.session_attributes['current_book_index'] = 0
    handler_input.attributes_manager.session_attributes['previous_intent'] = ""
    handler_input.response_builder.speak(speech_text).set_should_end_session(False).ask(ask_text)
    if is_apl_supported(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_launch_bestseller.json")['document'],
                    datasources=load_apl_document("apl_launch_bestseller.json")['datasources']
                )
        )
    return handler_input.response_builder.response

def handle_get_categories(handler_input):
    print('message from function = {0}'.format('handle_get_categories'))
    ask_text = " To know more about books, you can say find books or to quit say stop."
    cat_list = get_categories()
    print('cat_list = {0}'.format(cat_list))
    if cat_list is not None:
        speech_text = "Here are the book categories, {0}".format(", ".join(cat_list))
        new_datasource = prepare_category_list(load_apl_document("apl_books_categories.json")['datasources'])
        handler_input.response_builder.speak(speech_text + ask_text).ask(ask_text).set_should_end_session(False)
        if is_apl_supported(handler_input):
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    token="listToken",
                    document=load_apl_document("apl_books_categories.json")['document'],
                    datasources=new_datasource
                )
            )
    else:
        speech_text = "Sorry could not get the categories. Please try again or to quit say Stop"
        handler_input.response_builder.speak(speech_text).ask(ask_text).set_should_end_session(False)
    return handler_input.response_builder.response

@sb.request_handler(can_handle_func=is_intent_name("GetBestSellerIntent"))
def get_bestsellers_intent_handler(handler_input):
    print(' message from function = {0}'.format('get_bestsellers_intent_handler'))
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
    speech_text = "Welcome to Best Media Info, to get the New York Times Best sellers list, you can say find books list"
    navigate_home_handler(handler_input, speech_text, 'you can say find books list for sports')
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input :
        is_intent_name("AMAZON.NavigateHomeIntent")(input) or
        is_intent_name("HomeIntent")(input))
def go_home_request_handler(handler_input):
    speech_text = "To get the New York Times Best sellers list you can say find books list for sports."
    navigate_home_handler(handler_input, speech_text, 'you can say find books list for sports')
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("Alexa.Presentation.APL.UserEvent"))
def alexa_user_event_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch

    print('message from function = {0}'.format('alexa_user_event_request_handler'))
    
    arguments = handler_input.request_envelope.request.arguments
    request_type = handler_input.request_envelope.request.object_type
    print('arguments = {0}'.format(arguments))

    if len(arguments) >= 3:
        item_selected = arguments[0]
        item_ordinal =  arguments[1]
        item_title   = arguments[2]

    if item_selected == "LogoItem":
        speech_text = "To get the New York Times Best sellers list, you can say find books list for sports."
        navigate_home_handler(handler_input, speech_text, speech_text)
        return handler_input.response_builder.response
        

    elif item_selected == 'LaunchTemplateItem':
        if item_title == 'Books':
            # Launch Book Category
            handle_get_categories(handler_input)
            return handler_input.response_builder.response

        if item_title == 'Movies':
            # Launch Book Category
            speech_text = "Following are brief movie reviews"
            handler_input.attributes_manager.session_attributes['previous_intent'] = 'MovieReviewIntent'
            res_reviews = requests.get(query_moview_reviews, params={'api-key': nyt_api_key}, timeout=60).json()
            if str.lower(res_reviews['status']) == 'ok':
                fill_movie_list(handler_input, res_reviews, 0)
            else:
                speech_text = "Sorry could find movie reviews at this time. Please try again"
                handler_input.response_builder.speak(speech_text).ask(speech_text)
    
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
        if 'movie_list' in handler_input.attributes_manager.persistent_attributes:
            movie_review_data = json.loads(handler_input.attributes_manager.persistent_attributes['movie_list'])
            movie_item  = movie_review_data['results'][item_ordinal]
            print('loading movie data {0}'.format(movie_item))
            movie_datasource = load_apl_document("apl_single_movie.json")['datasources']
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
    handle_get_categories(handler_input)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    speech_text = "Best Media Info provides information about New York Times best seller books list and moview reviews, " +\
    "books are devided in categories for example sports, travel, and science. " +\
    "To know about books you can say find book for sports, To know about book categories say Get categories." +\
    " or To get movie reviews please say get move review"
    ask_text = 'Sorry I did not get it. To get book say find books for tavel '
    handler_input.response_builder.speak(speech_text).ask(speech_text)
    if is_apl_supported(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="pagerToken",
                document=load_apl_document("apl_help_view.json")['document'],
                datasources=load_apl_document("apl_help_view.json")['datasources']
            )
    )
    return handler_input.response_builder.response



@sb.request_handler(can_handle_func=is_intent_name("AMAZON.YesIntent"))
def yes_intent_handler(handler_input):
    print(' message from function = {0}'.format('yes_intent_handler'))
    sorry_text = 'Sorry, I did not get it. if you want to know the categories you can say get book categories'
    attr = handler_input.attributes_manager.persistent_attributes
    sess_attr = handler_input.attributes_manager.session_attributes
    if sess_attr['previous_intent'] == 'MovieReviewIntent':
        try:
            if attr['movie_list'] is None:
                attr['movie_list'] = requests.get(query_moview_reviews, params={'api-key': nyt_api_key}, timeout=60).json()
        except Exception as ex:
            print('Source = {0}, Error = {1}'.format('launch_request_handler', ex.args[0]))

        fill_movie_list(handler_input, json.loads(attr['movie_list']), sess_attr['current_movie_index'])
        return handler_input.response_builder.response
    else:
        handler_input.response_builder.speak(sorry_text).ask(sorry_text)

    handler_input.attributes_manager.save_persistent_attributes()
    return handler_input.response_builder.response

#***************************Movie Review *******************************************************


def fill_movie_list(handler_input, res_reviews, start_index=0):
    review_text_list = list()
    print(" message from function = {0} start_index = {1}".format("fill_movie_list", start_index))
    # will pick any 5 moview review randomly
    data_source = load_apl_document('apl_movie_list.json')['datasources']
    data_movie_list = data_source['listTemplate1ListData']['listPage']['listItems']
    max_count = start_index + 5 if len(res_reviews['results']) > start_index + 5 else len(res_reviews['results'])
    movie_data_attr = list()
    movie_index_selected = list()
    handler_input.attributes_manager.session_attributes['current_movie_index'] = max_count
    if start_index < len(res_reviews['results']):
        for i in range(start_index, max_count):
            movie_item = res_reviews['results'][i]
            review_text = 'Movie name is {0}. Number of critics pick is {1}, opening date of movie is {2} and summery is. {3}. '.format(
                movie_item['display_title'], movie_item['critics_pick'], movie_item['opening_date'],
                movie_item['summary_short']
            )
            review_text_list.append(review_text)
    
            # fill APL Template
            print(review_text)
            # only five elements
            data_movie_list[i-start_index]['ordinal'] = i + 1
            data_movie_list[i-start_index]['listItemIdentifier'] = i
            data_movie_list[i-start_index]['textContent']['primaryText']['text'] = movie_item['display_title']
            data_movie_list[i-start_index]['textContent']['secondaryText']['text'] = movie_item['headline']
            # for session attribute
            movie_data_attr.append(movie_item)
    
        
        handler_input.attributes_manager.session_attributes['movie_review_data'] = movie_data_attr
        handler_input.attributes_manager.session_attributes['movie_index_selected'] = movie_index_selected
        data_source['listTemplate1ListData']['listPage']['listItems'] = data_movie_list
        if max_count < len(res_reviews['results']):
            ask_text = ' To know more movies, please say Yes, to quit say no'
            speech_text = 'Movie reviews from New York Times. {0}. {1} '.format(
            ", ".join(review_text_list), ask_text)
            if is_apl_supported(handler_input):
                handler_input.response_builder.speak(speech_text).ask(ask_text).set_should_end_session(False).add_directive(
                    RenderDocumentDirective(
                        token="listToken",
                        document=load_apl_document('apl_movie_list.json')['document'],
                        datasources=data_source
                    )
                )
        else:
            ask_text ="To start again you can say go home, to quit say stop"
            speech_text = " {0}. That's all I have for movies. To know about books you can yes get books list for science. To quit you can say stop. ".format(
                ", ".join(review_text_list))
            if is_apl_supported(handler_input):
                handler_input.response_builder.speak(speech_text).ask(ask_text).set_should_end_session(False).add_directive(
                    RenderDocumentDirective(
                        token="listToken",
                        document=load_apl_document('apl_movie_list.json')['document'],
                        datasources=data_source
                    )
                )
    else:
        # this case will happen when all reviews are done but user says Yes
        speech_text = "That's all I have for movies. To know about books you can yes get books list for science. To quit you can say stop."
        handler_input.response_builder.speak(speech_text).ask(speech_text).set_should_end_session(False)
    

    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("MovieReviewIntent"))
def get_movie_review_intent_handler(handler_input):
    print(' message from function = {0}'.format('get_movie_review_intent_handler'))
    speech_text = ""

    res_reviews = requests.get(query_moview_reviews, params={'api-key': nyt_api_key}, timeout=60).json()
    handler_input.attributes_manager.session_attributes['previous_intent'] = 'MovieReviewIntent'

    if str.lower(res_reviews['status']) == 'ok':
        fill_movie_list(handler_input, res_reviews, 0)
    else:
        speech_text = "Sorry could find movie reviews at this time. Please try again"
        handler_input.response_builder.speak(speech_text).ask(speech_text)
    handler_input.attributes_manager.persistent_attributes['movie_list'] = json.dumps(res_reviews)
    handler_input.attributes_manager.save_persistent_attributes()
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input :
    is_intent_name("AMAZON.StopIntent")(input) or
    is_intent_name("AMAZON.NoIntent")(input) or
    is_intent_name("AMAZON.NoIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    print(' message from function = {0}'.format('cancel_and_stop_intent_handler'))
    speech_text = "Goodbye!"
    if is_apl_supported(handler_input):
        handler_input.response_builder.add_directive(
            RenderDocumentDirective(
                token="pagerToken",
                document=load_apl_document("apl_goodbye_view.json")["document"],
                datasources=load_apl_document("apl_goodbye_view.json")["datasources"]
                )
        )
    
    handler_input.response_builder.speak(speech_text).set_should_end_session(True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    #any cleanup logic goes here

    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Log the exception in CloudWatch Logs
    print(exception)

    speech = "Sorry, There is some problem in getting your request. Can you please say it again!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


handler = sb.lambda_handler()

