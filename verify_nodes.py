from asl3_wx_announce.narrator import Narrator

def test_startup():
    config = {'station': {'callsign': 'TEST', 'report_style': 'quick'}}
    narrator = Narrator(config)
    
    # Test case: node 1966
    city = "TestCity"
    interval = 10
    nodes = ["1966", "2020"]
    source = "Test Source"
    
    msg = narrator.get_startup_message(city, interval, nodes, source)
    print("Startup Message:")
    print(msg)
    
    expected_snippet_1 = "1 9 6 6"
    expected_snippet_2 = "2 0 2 0"
    
    if expected_snippet_1 in msg and expected_snippet_2 in msg:
        print("\nSUCCESS: Nodes are formatted as digits.")
    else:
        print("\nFAILURE: Nodes are NOT formatted correctly.")

if __name__ == "__main__":
    test_startup()
