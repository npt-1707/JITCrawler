    re.compile(
        r'^diff --git "a/(?P<from_file>.*?)"\s* "b/(?P<to_file>.*?)"\s*$'),
    re.compile(
        r'^diff --git a/(?P<from_file>.*?)\s* "b/(?P<to_file>.*?)"\s*$'),
    re.compile(
        r'^diff --git "a/(?P<from_file>.*?)"\s* b/(?P<to_file>.*?)\s*$'),
    r"^index (?P<from_blob>.*?)\.\.(?P<to_blob>.*?)(?: (?P<mode>\d+))?$")

        return "Line {}: {}".format(self.line,
                                    super(LineParseError, self).__str__())
            raise LineParseError("{} ({!r})".format(parse_exc, line),
                                 line_index + 1)
            "start_of_file",
            "new_mode_header",
            "line_diff",
            "no_newline",
            "index_diff_header",
            "binary_diff",
            "rename_b_file",
            "rename_b_file",
            "file_diff_header",
            "new_mode_header",
            "new_file_mode_header",
            "deleted_file_mode_header",