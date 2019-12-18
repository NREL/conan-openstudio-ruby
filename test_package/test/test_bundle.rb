require 'minitest/autorun'
require 'fileutils'
require 'tmpdir'

# test bundle capability in CLI
# currently CLI cannot do bundle install, rely on system bundle for that for now
# in future, bundle install should be done like: openstudio --bundle_install Gemfile --bundle_path ./test_gems
class Bundle_Test < Minitest::Test

  def setup
    @cli_path = File.expand_path(File.join(File.dirname(__FILE__), '..', '/bin/openstudio'))
  end


  def rm_if_exist(p)
    if File.exist?(p)
      # comment out if you want to test without rebundling
      FileUtils.rm_rf(p)
    end
  end

  def prepare_test_folder(folder_name)
    # This folder contains the test.rb and the Gemfile needed to run the test
    ori_folder = File.join(File.dirname(__FILE__), folder_name)

    # Get a temp folder, and use that for testing
    # eg: On Ubuntu: "/tmp/bundle20191218-30742-1dinigo"
    #     On Win10: C:/Users/julien/AppData/Local/Temp/bundle20191218-30742-1dinigo
    test_folder = Dir.mktmpdir(folder_name)
    puts "Running '#{folder_name}' test in '#{test_folder}'"

    # Copy content of ori_folder to test_folder
    # same as cp -R ori_folder/* test_folder/
    # FileUtils.cp_r File.join(ori_folder, '/.'), test_folder

    # Just to be safe (in case user **previously** ran test_package locally
    # before this change meaning in-place, they might have Gemfile.lock,
    # so I'll specifically look for Gemfile and test.rb only
    file_list = ["Gemfile", "test.rb"].map{|f| File.join(ori_folder, f)}.select{|f| File.exists?(f)}
    # assert(file_list.size > 0)
    FileUtils.cp_r(file_list, test_folder)

    # When we're done, we'll remove the tmp dir
    at_exit  { FileUtils.remove_entry(test_folder) }

    return test_folder
  end

  # A temp workaround to remove the BUNDLED_WITH version
  # https://github.com/NREL/openstudio-gems/pull/10
  def temp_fixing_bundler_version(test_folder)
    lockfile = File.join(test_folder, "Gemfile.lock")
    content = File.read(lockfile)
    content.gsub!(/BUNDLED WITH\s+\d.\d.\d\s*/m, "")
    File.open(lockfile, "w") {|f| f.puts content }
  end

  def test_bundle
    original_dir = Dir.pwd

    test_folder = prepare_test_folder('bundle')
    Dir.chdir(test_folder)

    # No need to... it's a temp folder
    #rm_if_exist('Gemfile.lock')
    #rm_if_exist('./test_gems')
    #rm_if_exist('./bundle')

    assert(system('bundle install --path ./test_gems'))
    assert(system('bundle lock --add_platform ruby'))
    temp_fixing_bundler_version(test_folder)
    assert(system("'#{@cli_path}' --bundle Gemfile --bundle_path './test_gems' --verbose test.rb"))

  ensure
    Dir.chdir(original_dir)
  end

  def test_bundle_git
    original_dir = Dir.pwd

    test_folder = prepare_test_folder('bundle_git')
    Dir.chdir(test_folder)

    assert(system('bundle install --path ./test_gems'))
    assert(system('bundle lock --add_platform ruby'))
    temp_fixing_bundler_version(test_folder)
    assert(system("'#{@cli_path}' --bundle Gemfile --bundle_path './test_gems' --verbose test.rb"))

  ensure
    Dir.chdir(original_dir)
  end

  def test_bundle_native
    original_dir = Dir.pwd

    if /mingw/.match(RUBY_PLATFORM) || /mswin/.match(RUBY_PLATFORM)
      skip("Native gems not supported on Windows")
    else
      skip("Native gems not supported on Unix or Mac")
    end

    test_folder = prepare_test_folder('bundle_native')
    Dir.chdir(test_folder)

    assert(system('bundle install --path ./test_gems'))
    #assert(system('bundle lock --add_platform ruby'))
    if /mingw/.match(RUBY_PLATFORM) || /mswin/.match(RUBY_PLATFORM)
      assert(system('bundle lock --add_platform mswin64'))
    end
    temp_fixing_bundler_version(test_folder)
    assert(system("'#{@cli_path}' --bundle Gemfile --bundle_path './test_gems' --verbose test.rb"))

  ensure
    Dir.chdir(original_dir)
  end

  def test_bundle_no_install
    original_dir = Dir.pwd

    test_folder = prepare_test_folder('bundle_no_install')
    Dir.chdir(test_folder)

    #assert(system('bundle install --path ./test_gems'))
    #assert(system('bundle lock --add_platform ruby'))

    # intentionally called with dependencies not found in the CLI, expected to fail
    assert_equal(system("'#{@cli_path}' --bundle Gemfile --verbose test.rb"), false)

  ensure
    Dir.chdir(original_dir)
  end

  def test_no_bundle
    original_dir = Dir.pwd

    test_folder = prepare_test_folder('no_bundle')
    Dir.chdir(test_folder)

    puts "'#{@cli_path}' --verbose test.rb"
    assert(system("'#{@cli_path}' --verbose test.rb"))

  ensure
    Dir.chdir(original_dir)
  end

end
