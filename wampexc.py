class WAMPError(Exception):

    def __init__(self, error_uri, error_desc, error_details=None):
        super(WAMPError, self).__init__(error_uri, error_desc, error_details)
        self.error_uri = error_uri
        self.error_desc = error_desc
        self.error_details = error_details
