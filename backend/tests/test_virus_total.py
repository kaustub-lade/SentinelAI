from app.services import virus_total


def test_vt_stub_without_key():
    # settings.VIRUSTOTAL_API_KEY is empty in default config; expect stub
    res = virus_total.lookup_file_hash("0123456789abcdef")
    assert isinstance(res, dict)
    assert res.get("error") == "no_api_key"
