from django.db import models
from comps.models.comp import Comp
from rankings.models import Dancer


class Heatlist_Dancer(models.Model):
    '''Define minimal info about a dancer read in from a heatlist.'''

    # the name field is in last, first middle format
    name = models.CharField(max_length=100, blank=True)

    # the code field is used to obtain scoresheet results for this dancer
    code = models.CharField(max_length = 20)

    # the dancer object that matches this name
    alias = models.ForeignKey("rankings.Dancer", on_delete=models.SET_NULL, null=True)

    # the comp object that created this heatlist_dancer
    comp = models.ForeignKey("comps.Comp", on_delete=models.CASCADE, null=True)

    # flag to indicate if the name needs additional formatting by the user
    formatting_needed = models.BooleanField(default=False)


    def format_name(self, orig_name, simple=True, split_on=1):
        '''This method converts a name into last, first format.
           If simple is true, the method will not attempt to format names with three or more fields.
           If simple is false, the split_on field will determine where to put the comma'''

        fields = orig_name.split()
        if simple:
            if len(fields) == 2:
                return fields[1] + ', '  + fields[0]
            else:
                print("format needed: " + orig_name)
                self.formatting_needed = True
                return None
        elif len(fields) == 1:
            return(orig_name)
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
            print("Error - invalid code")


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


    def load_from_ndca_premier_feed(self, json_record):
        '''This method populates the object from a JSON object from a heatlist in NDCA Premier format.'''
        # find the dancer's name
        name_field = json_record["Name"]
        if len(name_field) == 2 and name_field[0] is not None and name_field[1] is not None:
            self.name = name_field[1] + ", " + name_field[0]
        else:
            self.formatting_needed = True
            self.name = name_field[0]
            for f in range(1, len(name_field)):
                if name_field[f] is not None:
                    self.name += " "
                    self.name += name_field[f]

        # find the ID code for this dancer
        self.code = json_record["ID"]


    def load_from_o2cm(self, line):
        '''This method populates the object from a line of text from a heatlist in o2cm.com format.'''
        # find the dancer's name
        fields = line.split(">")
        self.name = fields[1]

        # find the ID code for this dancer
        pos = fields[0].find("VALUE=") + len("VALUE=")
        self.code = fields[0][pos+1:-1]


    def load_from_file(self, line):
        '''This method populates the object from a line of text from a heatlist in custom file format.'''
        # find the dancer's name
        fields = line.split(":")
        self.name = fields[0]
        self.code = fields[1]


    def __str__(self):
        return self.name + ' ' + str(self.comp)

    class Meta:
        ordering = ['comp']