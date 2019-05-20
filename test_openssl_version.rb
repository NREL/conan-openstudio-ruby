require 'openssl'

# Expects one argument: the OpenSSL version, eg "1.1.0g"
expected_v = ARGV[0]

if expected_v.nil? or (not expected_v.match(/\d+\.\d+\.\d+[a-z]/))
  raise "Wrong expected version '#{expected_v}'"
end

v = OpenSSL::OPENSSL_VERSION[/\d+\.\d+\.\d+[a-z]/]

if v == expected_v
  puts "OK OpenSSL Version match: '#{v}'"
else
  raise "Version Mismatch: expected '#{expected_v}', got '#{v}'"
end
