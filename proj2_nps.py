#################################
##### Name: Yash Kamat ##########
##### Uniqname: ykamat ##########
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets as secrets# file that contains your API key

# Global Variables
# CACHE_PATH = '/Users/yashkamat/Development/si507/projects/project2/Project2Winter2021/cache.json'
# API_CACHE_PATH = '/Users/yashkamat/Development/si507/projects/project2/Project2Winter2021/api_cache.json'

CURR_CACHE = {}
CURR_API_CACHE = {}

HOME_URL = 'https://www.nps.gov'

def save_cache(cache_dic, path):

    """
    Saves a specific dictionary to local directory as cache.

    Parameters
    ----------
    cache_dic: dict
        The dictionary to be cached.

    path: string
        The path where the dictionary should be cached.

    Returns
    -------
    None
    """

    with open(path, 'w') as outfile:
        cache = json.dump(cache_dic, outfile)

def load_cache(path):

    """
    Returns a dictionary representation of a local cache file.

    Parameters
    ----------
    path: string
        The path to the locally saved cache file.

    Returns
    -------
    cache_dic: dict
        Dictionary representation of the loaded cache.
    """

    with open(path) as json_file:
        cache_dic = json.load(json_file)
    return cache_dic

def get_url(url,cache_dic):

    """
    Fetches a URL if its repsonse is not in the cache.
    If the URL is in the current cache, it retrieves the response from it.

    Parameters
    ----------
    url: string
        The requested URL to be fetched.
    cache_dic: dict
        Dictionary representation of the current cache.

    Returns
    -------
    cache_dic[url]: string
        String representation of the response text for the requested url.
    """

    if url in cache_dic.keys():
        print('Using cache')
    else:
        print("Fetching")
        cache_dic[url] = requests.get(url).text
    return cache_dic[url]

def get_api(zipcode,cache_dic,params):

    """
    Makes a call to the MapQuest API if the requested zipcode doesn't exist in the local cache.
    If zipcode exists in local cache, retrieves the API response from cache.

    Parameters
    ----------
    zipcode: string
        The requested zipcode to be searched.
    cache_dic: dict
        Current API cache represented as a dictionary.
    params:
        Parameters for MapQuest API request.

    Returns
    -------
    cache_dic[zipcode]: JSON representation of API reqest repsonse.
    """

    if zipcode in cache_dic.keys():
        print('Using cache')
    else:
        print("Fetching")
        cache_dic[zipcode] = requests.get('http://www.mapquestapi.com/search/v2/radius', params=params).text

    return cache_dic[zipcode]

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self,category=None,name=None,address=None,zipcode=None,phone=None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f'{self.name} ({self.category}): {self.address} {self.zipcode}'

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    response = requests.get(HOME_URL).text
    soup = BeautifulSoup(response,'html.parser')
    state_list = soup.find('ul',class_='dropdown-menu SearchBar-keywordSearch').find_all('li')

    links = {}

    for item in state_list:
        key = str(item.text).lower()
        value = item.find('a').get('href')
        links[key] = HOME_URL + value

    return links

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''

    response = get_url(site_url,CURR_CACHE)
    soup = BeautifulSoup(response, 'html.parser')

    # Category
    try:
        category = soup.find("span", class_="Hero-designation").text.strip()
    except:
        category = ''

    # Name
    try:
        name = soup.find("a", class_="Hero-title").text.strip()
    except:
        name = ''

    # Address
    try:
        city = soup.find("span", itemprop="addressLocality").text.strip()
    except:
        city = ''

    try:
        state = soup.find("span", itemprop='addressRegion').text.strip()
    except:
        state = ''
    address = f'{city}, {state}'

    # Zipcode
    try:
        zipcode = soup.find("span", itemprop='postalCode').text.strip()
    except:
        zipcode = ''

    # Phone
    try:
        phone = soup.find("span", class_='tel').text.strip()
    except:
        phone = ''

    return NationalSite(category=category, name=name,address=address,zipcode=zipcode,phone=phone)

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    sites_list = []
    home_url = 'https://www.nps.gov'

    response = requests.get(state_url)
    soup = BeautifulSoup(response.text,'html.parser')

    for ref in soup.find('ul', id='list_parks').find_all('h3'):
        site_url = home_url+ref.find('a')['href']
        sites_list.append(get_site_instance(site_url))

    return sites_list

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''

    params = {'key': secrets.API_KEY,
           'radius': '10',
           'origin': site_object.zipcode,
           'maxMatches': '10',
           'ambiguities': 'ignore',
           'outFormat': 'json'}

    response = get_api(zipcode=site_object.zipcode, cache_dic=CURR_API_CACHE, params=params)
    return json.loads(response)

def print_sites(site_list):

    """
    Prints a formatted list of NationalSite objects.

    Parameters
    ----------
    site_list: list
        List of NationalSite objects.

    Returns
    -------
    None.
    """

    for site in site_list:
        pos = site_list.index(site)
        print(f'[{pos+1}] {site.info()}')

def print_nearby(api_dict):

    """
    Prints a formatted list of 'nearby locations' from an API response.

    Parameters
    ----------
    api_dict: dict
        Dictionary represenation of an API reponse for locations near a specific zipcode.

    Returns
    -------
    None.
    """

    for result in api_dict['searchResults']:
        name = result['name']
        address = result['fields']['address']
        category = result['fields']['group_sic_code_name_ext']
        city = result['fields']['city']
        if (len(name) > 0) and (len(category) > 0) and (len(address) > 0):
            print(f'- {name} ({category}): {address}, {city}')
        else:
            if (len(name) == 0):
                name = "no name"
            if (len(category) == 0):
                category = "no category"
            if (len(address) == 0):
                address = "no address"
            if (len(city) == 0):
                city = 'no city'
            print(f'- {name} ({category}): {address}, {city}')

def user_interface():

    """
    Runs the user facing loop to fetch sites or nearby locations for specific states/sites.
    Has no parameters or returns.

    """

    try:
        CURR_CACHE =  load_cache(CACHE_PATH)
    except:
        CURR_CACHE =  {}

    try:
        CURR_API_CACHE =  load_cache(API_CACHE_PATH)
    except:
        CURR_API_CACHE =  {}

    state_urls = build_state_url_dict()

    while True:
        state = input('Enter a state name (e.g. Michigan, michigan) or "exit": ')

        if state == "exit":
            quit()

        elif state.lower() not in state_urls.keys():
            print('[Error] Enter proper state name')

        else:
            s_list = get_sites_for_state(state_urls[state.lower()])
            print('\n-------------------------')
            print(f'List of national sites in {state}')
            print('-------------------------')
            print_sites(s_list)

            while True:
                choice = input('Choose the number for detail search or "exit" or "back": ')

                if choice == "exit":
                    quit()

                elif choice == "back":
                    break

                elif choice.isnumeric() == True:
                    if(int(choice) <= (len(s_list)+1)):
                        print('\n-------------------------')
                        print(f'Places near {s_list[(int(choice) - 1)].name}')
                        print('-------------------------')
                        print_nearby(get_nearby_places(s_list[(int(choice) - 1)]))
                        print('')
                    else:
                        print('\n[Error] Invalid input\n-------------------------')
                else:
                    print('\n[Error] Invalid input\n-------------------------')

if __name__ == "__main__":
    user_interface()