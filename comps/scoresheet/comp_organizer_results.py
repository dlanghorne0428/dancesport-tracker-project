import requests
import logging
from comps.scoresheet.results_processor import Results_Processor

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CompOrgResults(Results_Processor):
    '''This class is derived from a Results_Processor base class.
       It parses a results file from a website in CompOrganizer.com format
       and extracts the results of the competition.'''

    def __init__(self):
        ''' Initialize the class.'''
        super().__init__()
        self.comp_name = None


    ############### PRIMARY ROUTINES  ####################################################
    # the following methods are called from the main GUI program.
    ######################################################################################
    def open(self, url):
        '''This routine opens a scoresheet from the given URL.
           It saves information such that we can request results for any
           dancer in the competition'''
        #extract comp name from URL
        response = requests.get(url)
        lines = response.text.splitlines()
        for l in lines:
            start_pos = l.find("getResults")
            if start_pos == -1:
                continue
            else:
                # this line is in this format:
                # getResultsCompetitors('beachbash2019')
                # extract the name from between the quotes
                start_pos += len("getResultsCompetitors('")
                end_pos = l.find("')", start_pos)
                self.comp_name = l[start_pos:end_pos]
                logger.debug(self.comp_name)
                break

        # build a base_url that can be used to grab results for individual dancers
        end_pos = url.find("/pages")
        self.base_url = url[:end_pos] + "/co/scripts/results_scrape2.php?comp=" + self.comp_name
        logger.info(self.base_url)


    def get_scoresheet(self, entry):
        '''This routine requests the scoresheet for a given entry in this heat
           and returns it to the calling routine for processing.'''
        # build the request field based on the numeric code found in the entry
        url = self.base_url + "&id=" + entry.code
        logger.debug("Requesting " + url)

        # Make the HTML request and the data is returned as text.
        return requests.get(url)
