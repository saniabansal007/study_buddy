import os
from utils import ok_file, read_file, chunk, UPLOAD_DIR, CHUNK_SZ, OVERLAP

# test ok_file function
def test_ok_file():
    print("testing_ok_file")

    assert ok_file("notes.pdf")== True,  "pdf should be allowed"
    assert ok_file("slides.pptx")== True,  "pptx should be allowed"
    assert ok_file("notes.txt")== True,  "txt should be allowed"
    assert ok_file("image.png")== False, "png should be rejected"
    assert ok_file("notes.PDF")== True,  "uppercase PDF should be allowed"
    assert ok_file("notes.final.pdf")== True, "multiple dots should work"

    print("all passed\n\n")


# test the chunk function
def test_chunk():
    print("testing chunk\n")

    text= "a" * 1000
    chunks= chunk(text)
    print(f"input length   : {len(text)}")
    print(f"number of chunks: {len(chunks)}")
    print(f"first chunk len: {len(chunks[0])}")
    print(f"last chunk len : {len(chunks[-1])}")


# read txt file
def test_read_txt():
    print("test_read_txt\n")

    # Write a temp txt file
    path = os.path.join(UPLOAD_DIR, "test_sample.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("  Hello from a text file.  \nSecond line here.\n")

    text = read_file(path, "txt")
    os.remove(path)

    print(f"  extracted: {repr(text)}")
    assert "Hello from a text file." in text, "txt content should be present"
    assert "Second line here." in text, "second line should be present"
    assert not text.startswith(" "), "leading whitespace should be stripped"
    print("  passed\n")

# run all 
if __name__ == "__main__":
    test_ok_file()
    test_chunk()
    test_read_txt()
    print("__all tests passed__")