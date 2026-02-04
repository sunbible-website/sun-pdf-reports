def get_data_query(language_id=1):
    """Returns the SQL query to fetch report data for a specific language ID."""
    return f"""
        SELECT
            readersdetail.readersdetailid,
            readersdetail.sectionid,
            readersdetail.unicodeid,
            readersdetail.pageorderby,

            readers.unicodeid AS sectionunicode,
            readers.sectionname,
            readers.subsectionname,
            readers.pdforderby,

            wordlists.word,
            wordlists.unicode_id_id,
            wordlists.unicode_id_id || '.svg' AS svgname,
            wordlists.related_meaning,
            wordlists.made_from_word_1,
            wordlists.made_from_word_2,
            wordlists.made_from_word_3,

            language.txt_readers_dict_cover_1,
            language.txt_page_no

        FROM sun.readersdetail
        JOIN sun.readers
            ON readersdetail.sectionid = readers.sectionid
            AND readers.languageid = 1
        JOIN sun.wordlists AS wordlists
            ON readersdetail.unicodeid = wordlists.unicode_id_id
        JOIN sun.language AS language
            ON wordlists.language_id_id = language.language_id
        WHERE wordlists.language_id_id = {language_id}
        ORDER BY readers.pdforderby, readersdetail.pageorderby ASC;
    """
