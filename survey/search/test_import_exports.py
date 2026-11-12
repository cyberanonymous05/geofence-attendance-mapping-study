"""Parser tests with in-memory FAKE rows (format check only; nothing is written to the corpus)."""
from import_exports import parse, lang_code
sc = 'Authors,Title,Year,Source title,DOI,Abstract,Cited by,Document Type,Language of Original Document\n"A","TEST geofence attendance",2024,"J Test","10.1234/Abc.1","An abstract, with a comma.",3,Article,English\n"B","No abstract paper",2023,"J Test",,"[No abstract available]",,Conference Paper,English\n'
ws = "PT\tTI\tPY\tSO\tDI\tAB\tTC\tDT\tLA\nJ\tTEST lora attendance\t2022\tTest J\t10.5555/xyz\tSome abstract text\t7\tArticle\tEnglish\n"
ie = 'Document Title,Authors,Publication Title,Publication Year,DOI,Abstract,Article Citation Count,Content Type\n"TEST gps attendance","X","Proc Test",2021,"https://doi.org/10.1109/TEST.2021.1","Abs here",2,Conferences\n'
a = parse("scopus", sc); assert len(a) == 2 and a[0]["doi"] == "10.1234/abc.1" and a[0]["cited_by"] == 3 and a[0]["abstract"] == "An abstract, with a comma." and a[1]["abstract"] == "" and a[1]["doi"] == ""
b = parse("wos", ws); assert len(b) == 1 and b[0]["year"] == 2022 and b[0]["doi"] == "10.5555/xyz" and b[0]["cited_by"] == 7
c = parse("ieee", ie); assert len(c) == 1 and c[0]["doi"] == "10.1109/test.2021.1" and c[0]["venue"] == "Proc Test"
assert lang_code("en") == "en"
print("all import tests passed")
