import logging
from django.db import models

# Get an instance of a logger
logger = logging.getLogger(__name__)


class Heatlist_Dancer(models.Model):
    '''Define minimal info about a dancer read in from a heatlist.'''

    # the name field is in last, first middle format
    name = models.CharField(max_length=100, blank=True)

    # the code field is used to obtain scoresheet results for this dancer
    code = models.CharField(max_length = 20)

    # flag to indicate if the name needs additional formatting by the user
    formatting_needed = models.BooleanField(default=False)


    def format_name(self, orig_name, simple=True, split_on=1):
        '''This method converts a name into last, first format.
           If simple is true, the method will not attempt to format names with three or more fields.
           If simple is false, the split_on field will determine where to put the comma'''

        fields = orig_name.split()
        if len(fields) == 1:
            return(orig_name)
        if simple:
            if len(fields) == 2:
                return fields[1] + ', '  + fields[0]
            else:
                debug.info("format needed:", orig_name)
                self.formatting_needed = True
                return None
        else:
            name = ""
            for f in range(split_on, len(fields)):
                if f > split_on:
                    name += " "
                name += fields[f]
            name += ","
            for f in range(0, split_on):
                name += " " + fields[f]
            return name


    def load_from_comp_mngr(self, line):
        '''This method populates the object from a line of text from a CompMngr heatlist.'''
        # get the name
        start_pos = 8
        end_pos = line.find("</td>")
        self.name = line[start_pos:end_pos]
        # find the code
        start_pos = line.find("TABLE_CODE_") + len("TABLE_CODE_")
        end_pos = line.find("'", start_pos)
        self.code = line[start_pos:end_pos]


    def load_from_comp_org(self, line):
        '''This method populates the object from a line of text from a heatlist in CompOrganizer format.'''
        # find the ID code for this dancer
        start_pos = line.find('"id":"') + len('"id":"')
        end_pos = line.find('"', start_pos)
        self.code = line[start_pos:end_pos]

        if self.code != "0":
            # find the dancer's name
            start_pos = line.find('"name":"') + len('"name":"')
            end_pos = line.find('"', start_pos)
            orig_name = line[start_pos:end_pos]
            new_name = self.format_name(orig_name)
            if new_name is None:
                self.name = orig_name
            else:
                self.name = new_name
        else:
            logger.error("Error - invalid code")


    def load_from_ndca_premier(self, line):
        '''This method populates the object from a line of text from a heatlist in NDCA Premier format.'''
        # find the dancer's name
        fields = line.split(">")
        orig_name = fields[1]
        new_name = self.format_name(orig_name)
        if new_name is None:
            self.name = orig_name
        else:
            self.name = new_name

        # find the ID code for this dancer
        pos = fields[0].find("competitor=") + len("competitor=")
        self.code = fields[0][pos+1:-1]


    def load_from_file(self, line):
        '''This method populates the object from a line of text from a heatlist in custom file format.'''
        # find the dancer's name
        fields = line.split(":")
        self.name = fields[0]
        self.code = fields[1]


    def __str__(self):
        return self.name
