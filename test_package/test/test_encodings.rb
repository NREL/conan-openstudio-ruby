require 'minitest/autorun'

# test encoding of strings returned from OpenStudio Ruby bindings
class Encoding_Test < Minitest::Test

  def test_encoding
    test_string = "Hello"
    assert_equal("UTF-8", test_string.encoding.to_s)
  end

  def test_encoding2
    test_string = "模型"
    assert_equal("UTF-8", test_string.encoding.to_s)
  end


  # In some cases, including the use of Dir.pwd, on Windows the string might
  # not be UTF-8 encoded
  def test_encoding_external

    s_utf8 = "AfolderwithspécialCHar#%ù/test.osm".encode(Encoding::UTF_8)
    s_windows_1252 = "Afolderwithsp\xE9cialCHar#%\xF9/test.osm".force_encoding(Encoding::Windows_1252)
    assert_equal(s_utf8, s_windows_1252.encode(Encoding::UTF_8))

  end

end
