#!/usr/bin/env ruby

########################################################################################################################
#  OpenStudio(R), Copyright (c) 2008-2019, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#  following conditions are met:
#
#  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#  disclaimer.
#
#  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided with the distribution.
#
#  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission from the respective party.
#
#  (4) Other than as required in clauses (1) and (2), distributions in any form of modifications or other derivative works
#  may not use the "OpenStudio" trademark, "OS", "os", or any other confusingly similar designation without specific prior
#  written permission from Alliance for Sustainable Energy, LLC.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
#  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########################################################################################################################

#File.open('E:\test\test.log', 'w') do |f|
#  ENV.each_key {|k| f.puts "#{k} = #{ENV[k]}" }
#end

#Signal.trap('INT') { abort }

require 'logger'
require 'optparse'
require 'stringio'
require 'rbconfig'

$argv = ARGV.dup

$logger = Logger.new(STDOUT)
#$logger.level = Logger::ERROR
$logger.level = Logger::WARN
#$logger.level = Logger::DEBUG

# debug Gem::Resolver, must go before resolver is required
#ENV['DEBUG_RESOLVER'] = "1"
original_arch = nil
if RbConfig::CONFIG['arch'] =~ /x64-mswin64/
  # assume that system ruby of 'x64-mingw32' architecture was used to create bundle
  original_arch = RbConfig::CONFIG['arch']
  RbConfig::CONFIG['arch'] = 'x64-mingw32'
end

# load embedded ruby gems
require 'rubygems'
require 'rubygems/version'
Gem::Platform.local

if original_arch
  RbConfig::CONFIG['arch'] = original_arch
end

module OpenStudio
  def self.getOpenStudioCLI
    return ENV["OS_CLI"]
  end
end

module Gem
class Specification < BasicSpecification
  def gem_dir
    embedded = false
    tmp_loaded_from = loaded_from.clone
    if tmp_loaded_from.chars.first == ':'
      tmp_loaded_from[0] = ''
      embedded = true
    end

    joined = File.join(gems_dir, full_name)
    if embedded
      test = /bundler\/gems/.match(tmp_loaded_from)
      if test
        @gem_dir = ':' + (File.dirname tmp_loaded_from)
      else
        @gem_dir = joined
      end
    else
      @gem_dir = File.expand_path joined
    end
  end

  def full_gem_path
    # TODO: This is a heavily used method by gems, so we'll need
    # to aleast just alias it to #gem_dir rather than remove it.
    embedded = false
    tmp_loaded_from = loaded_from.clone
    if tmp_loaded_from.chars.first == ':'
      tmp_loaded_from[0] = ''
      embedded = true
    end

    joined = File.join(gems_dir, full_name)
    if embedded
      test = /bundler\/gems/.match(tmp_loaded_from)
      if test
        @full_gem_path = ':' + (File.dirname tmp_loaded_from)
        @full_gem_path.untaint
        return @full_gem_path
      else
        @full_gem_path = joined
        @full_gem_path.untaint
        return @full_gem_path
      end
    else
      @full_gem_path = File.expand_path joined
      @full_gem_path.untaint
    end
    return @full_gem_path if File.directory? @full_gem_path

    @full_gem_path = File.expand_path File.join(gems_dir, original_name)
  end

  def gems_dir
    # TODO: this logic seems terribly broken, but tests fail if just base_dir
    @gems_dir = File.join(loaded_from && base_dir || Gem.dir, "gems")
  end

  def base_dir
    return Gem.dir unless loaded_from

    embedded = false
    tmp_loaded_from = loaded_from.clone
    if tmp_loaded_from.chars.first == ':'
      tmp_loaded_from[0] = ''
      embedded = true
    end

    test = /bundler\/gems/.match(tmp_loaded_from)
    result = if (default_gem? || test) then
        File.dirname File.dirname File.dirname tmp_loaded_from
      else
        File.dirname File.dirname tmp_loaded_from
      end

    if embedded
      result = ':' + result
    end
    @base_dir = result
  end

end
end

# have to do some forward declaration and pre-require to get around autoload cycles
#module Bundler
#end

# This is the code chunk to allow for an embedded IRB shell. From Jason Roelofs, found on StackOverflow
module IRB # :nodoc:
  def self.start_session(binding)
    unless @__initialized
      args = ARGV
      ARGV.replace(ARGV.dup)
      IRB.setup(nil)
      ARGV.replace(args)
      @__initialized = true
    end

    workspace = WorkSpace.new(binding)

    irb = Irb.new(workspace)

    @CONF[:IRB_RC].call(irb.context) if @CONF[:IRB_RC]
    @CONF[:MAIN_CONTEXT] = irb.context

    catch(:IRB_EXIT) do
      irb.eval_input
    end
  end
end

# This is the save puts to use to catch EPIPE. Uses `puts` on the given IO object and safely ignores any Errno::EPIPE
#
# @param [String] message Message to output
# @param [Hash] opts Options hash
#
def safe_puts(message=nil, opts=nil)
  message ||= ''
  opts = {
      io: $stdout,
      printer: :puts
  }.merge(opts || {})

  begin
    opts[:io].send(opts[:printer], message)
  rescue Errno::EPIPE
    # This is what makes this a `safe` puts
    return
  end
end

# This is a convenience method that properly handles duping the originally argv array so that it is not destroyed. This
# method will also automatically detect "-h" and "--help" and print help. And if any invalid options are  detected, the
# help will be printed, as well
#
# @param [Object, nil] opts An instance of OptionParse to parse against, defaults to a new OptionParse instance
# @param [Array, nil] argv The argv input to be parsed, defaults to $argv
# @return[Array, nil] If this method returns `nil`, then you should assume that help was printed and parsing failed
#
def parse_options(opts=nil, argv=nil)
  # Creating a shallow copy of the arguments so the OptionParser
  # doesn't destroy the originals.
  argv ||= $argv.dup

  # Default opts to a blank optionparser if none is given
  opts ||= OptionParser.new

  # Add the help option, which must be on every command.
  opts.on_tail('-h', '--help', 'Print this help') do
    safe_puts(opts.help)
    return nil
  end

  opts.parse!(argv)
  return argv
rescue OptionParser::InvalidOption, OptionParser::MissingArgument
  raise "Error: Invalid CLI option, #{opts.help.chomp}"
end

# This method will split the argv given into three parts: the flags to this command, the command, and the flags to
# the command. For example:
#     -v status -h -v
# The above would yield 3 parts:
#     ["-v"]
#     "status"
#     ["-h", "-v"]
# These parts are useful because the first is a list of arguments given to the current command, the second is a
# command, and the third are the commands given to the command
#
# @param [Array] argv The input to be split
# @param [Array] command_list Hash of commands to look for
# @return [Array] The split command as [main arguments, sub command, sub command arguments]
#
def split_main_and_subcommand(argv, command_list)
  # Initialize return variables
  main_args   = nil
  sub_command = nil
  sub_args    = []

  commands = []
  command_list.keys.each {|k| commands << k.to_s}

  # We split the arguments into two: One set containing any flags before a word, and then the rest. The rest are what
  # get actually sent on to the command
  argv.each_index do |i|
    if commands.index(argv[i])
      main_args   = argv[0, i]
      sub_command = argv[i]
      sub_args    = argv[i+1..-1]
      break
    elsif argv[i].end_with?('.rb')
      main_args   = argv[0, i]
      sub_command = 'execute_ruby_script'
      sub_args    = argv[i..-1]
      break
    end
  end

  # Handle the case that argv was empty or didn't contain any command
  main_args = argv.dup if main_args.nil?

  [main_args, sub_command, sub_args]
end

# parse the main args, those that come before the sub command
def parse_main_args(main_args)

  $logger.debug "Parsing main_args #{main_args}"

  # verbose already handled
  main_args.delete('--verbose')

  # Operate on the include option to add to $LOAD_PATH
  remove_indices = []
  new_path = []
  main_args.each_index do |i|

    if main_args[i] == '-I' || main_args[i] == '--include'
      # remove from further processing
      remove_indices << i
      remove_indices << i+1

      dir = main_args[i + 1]

      if dir.nil?
        $logger.error "#{main_args[i]} requires second argument DIR"
        return false
      elsif !File.exists?(dir) || !File.directory?(dir)
        # DLM: Ruby doesn't warn for this
        #$logger.warn "'#{dir}' passed to #{main_args[i]} is not a directory"
      end
      new_path << dir
    elsif main_args[i] == '--no-ssl'
      $logger.warn "'--no-ssl' flag is deprecated"
    end
  end

  remove_indices.reverse_each {|i| main_args.delete_at(i)}

  if !new_path.empty?

    new_path = new_path.concat($LOAD_PATH)

    $logger.info "Setting $LOAD_PATH to #{new_path}"
    $LOAD_PATH.clear

    new_path.each {|p| $LOAD_PATH << p}
  end

  # Operate on the gem_path option to set GEM_PATH
  remove_indices = []
  new_path = []
  main_args.each_index do |i|

    if main_args[i] == '--gem_path'

      # remove from further processing
      remove_indices << i
      remove_indices << i+1

      dir = main_args[i + 1]

      if dir.nil?
        $logger.error "#{main_args[i]} requires second argument DIR"
        return false
      elsif !File.exists?(dir) || !File.directory?(dir)
        # DLM: Ruby doesn't warn for this
        #$logger.warn "'#{dir}' passed to #{main_args[i]} is not a directory"
      end
      new_path << dir
    end
  end
  remove_indices.reverse_each {|i| main_args.delete_at(i)}

  if !new_path.empty?
    if ENV['GEM_PATH']
      new_path << ENV['GEM_PATH'].to_s
    end

    new_path = new_path.join(File::PATH_SEPARATOR)

    $logger.info "Setting GEM_PATH to #{new_path}"
    ENV['GEM_PATH'] = new_path
  end

  # Operate on the gem_home option to set GEM_HOME
  if main_args.include? '--gem_home'
    option_index = main_args.index '--gem_home'
    path_index = option_index + 1
    new_home = main_args[path_index]
    main_args.slice! path_index
    main_args.slice! main_args.index '--gem_home'

    $logger.info "Setting GEM_HOME to #{new_home}"
    ENV['GEM_HOME'] = new_home
  end

  # Operate on the bundle option to set BUNDLE_GEMFILE
  use_bundler = false
  if main_args.include? '--bundle'
    option_index = main_args.index '--bundle'
    path_index = option_index + 1
    gemfile = main_args[path_index]
    main_args.slice! path_index
    main_args.slice! main_args.index '--bundle'

    $logger.info "Setting BUNDLE_GEMFILE to #{gemfile}"
    ENV['BUNDLE_GEMFILE'] = gemfile
    use_bundler = true

  elsif ENV['BUNDLE_GEMFILE']
    # no argument but env var is set
    $logger.info "ENV['BUNDLE_GEMFILE'] set to '#{ENV['BUNDLE_GEMFILE']}'"
    use_bundler = true

  end

  if main_args.include? '--bundle_path'
    option_index = main_args.index '--bundle_path'
    path_index = option_index + 1
    bundle_path = main_args[path_index]
    main_args.slice! path_index
    main_args.slice! main_args.index '--bundle_path'

    $logger.info "Setting BUNDLE_PATH to #{bundle_path}"
    ENV['BUNDLE_PATH'] = bundle_path

  elsif ENV['BUNDLE_PATH']
    # no argument but env var is set
    $logger.info "ENV['BUNDLE_PATH'] set to '#{ENV['BUNDLE_PATH']}'"

  elsif use_bundler
    # bundle was requested but bundle_path was not provided
    $logger.warn "Bundle activated but ENV['BUNDLE_PATH'] is not set"

    $logger.info "Setting BUNDLE_PATH to ':/ruby/2.7.0/'"
    ENV['BUNDLE_PATH'] = ':/ruby/2.7.0/'

  end

  if main_args.include? '--bundle_without'
    option_index = main_args.index '--bundle_without'
    path_index = option_index + 1
    bundle_without = main_args[path_index]
    main_args.slice! path_index
    main_args.slice! main_args.index '--bundle_without'

    $logger.info "Setting BUNDLE_WITHOUT to #{bundle_without}"
    ENV['BUNDLE_WITHOUT'] = bundle_without

  elsif ENV['BUNDLE_WITHOUT']
    # no argument but env var is set
    $logger.info "ENV['BUNDLE_WITHOUT'] set to '#{ENV['BUNDLE_WITHOUT']}'"

  elsif use_bundler
    # bundle was requested but bundle_path was not provided
    $logger.warn "Bundle activated but ENV['BUNDLE_WITHOUT'] is not set"

    # match configuration in build_openstudio_gems
    $logger.info "Setting BUNDLE_WITHOUT to 'test'"
    ENV['BUNDLE_WITHOUT'] = 'test'

    # ignore any local config on disk
    #DLM: this would be correct if the bundle was created here
    #it would not be correct if the bundle was transfered from another computer
    #ENV['BUNDLE_IGNORE_CONFIG'] = 'true'
  Gem.paths.path << ':/ruby/2.2.0/bundler/gems/'

  end

  Gem.paths.path << ':/ruby/2.7.0/gems/'
  Gem.paths.path << ':/ruby/2.7.0/bundler/gems/'

  # find all the embedded gems
  original_embedded_gems = {}

  # Add the gem spec paths. This filepath name gets appended with 'specification' 
  # This will trigger Gem to reload all gems in these paths. 
  Gem::Specification.dirs=( [":/ruby/2.7.0", ":/ruby/2.7.0/gems", ":/ruby/2.7.0/bundler/gems" ] ) 
  
  # activate or remove bundler
  Gem::Specification.each do |spec|
    if spec.gem_dir.chars.first == ':'
      if spec.name == 'bundler'
        if use_bundler
          spec.activate
        else
          # DLM: don't remove, used by Resolver
          #Gem::Specification.remove_spec(spec)
        end
      end
    end
  end

  if use_bundler

    current_dir = Dir.pwd

    original_arch = nil
    if RbConfig::CONFIG['arch'] =~ /x64-mswin64/
      # assume that system ruby of 'x64-mingw32' architecture was used to create bundle
      original_arch = RbConfig::CONFIG['arch']
      $logger.info "Temporarily replacing arch '#{original_arch}' with 'x64-mingw32' for Bundle"
      RbConfig::CONFIG['arch'] = 'x64-mingw32'
    end



    # require bundler
    # have to do some forward declaration and pre-require to get around autoload cycles
    require 'bundler/errors'
    #require 'bundler/environment_preserver'
    require 'bundler/plugin'
    #require 'bundler/rubygems_ext'
    require 'bundler/rubygems_integration'
    require 'bundler/version'
    require 'bundler/ruby_version'
    #require 'bundler/constants'
    #require 'bundler/current_ruby'
    require 'bundler/gem_helpers'
    #require 'bundler/plugin'
    require 'bundler/source'
    require 'bundler/definition'
    require 'bundler/dsl'
    require 'bundler/uri_credentials_filter'
    require 'bundler'

    begin
      # activate bundled gems
      # bundler will look in:
      # 1) ENV["BUNDLE_GEMFILE"]
      # 2) find_file("Gemfile", "gems.rb")
      #require 'bundler/setup'

      groups = Bundler.definition.groups
      keep_groups = []
      without_groups = ENV['BUNDLE_WITHOUT']
      $logger.info "without_groups = #{without_groups}"
      groups.each do |g|
        $logger.info "g = #{g}"
        if without_groups.include?(g.to_s)
          $logger.info "Bundling without group '#{g}'"
        else
          keep_groups << g
      end
      end

      $logger.info "Bundling with groups [#{keep_groups.join(',')}]"

      remaining_specs = []
      Bundler.definition.specs_for(keep_groups).each {|s| remaining_specs << s.name}

      $logger.info "Specs to be included [#{remaining_specs.join(',')}]"

      Bundler.setup(*keep_groups)
      #Bundler.require(*keep_groups)

    #rescue Bundler::BundlerError => e

      #$logger.info e.backtrace.join("\n")
      #$logger.error "Bundler #{e.class}: Use `bundle install` to install missing gems"
      #exit e.status_code

    ensure

      if original_arch
        $logger.info "Restoring arch '#{original_arch}'"
        RbConfig::CONFIG['arch'] = original_arch
      end

      Dir.chdir(current_dir)
    end

  else
    # not using_bundler

    current_dir = Dir.pwd

    begin
      # DLM: test code, useful for testing from command line using system ruby
      #Gem::Specification.each do |spec|
      #  if /openstudio/.match(spec.name)
      #    original_embedded_gems[spec.name] = spec
      #  end
      #end

      # get a list of all the embedded gems
      dependencies = []
      original_embedded_gems.each_value do |spec|
        $logger.debug "Adding dependency on #{spec.name} '~> #{spec.version}'"
        dependencies << Gem::Dependency.new(spec.name, "~> #{spec.version}")
      end
      #dependencies.each {|d| $logger.debug "Added dependency #{d}"}

      # resolve dependencies
      activation_errors = false
      original_load_path = $:.clone
      resolver = Gem::Resolver.for_current_gems(dependencies)
      activation_requests = resolver.resolve
      $logger.debug "Processing #{activation_requests.size} activation requests"
      activation_requests.each do |request|
        do_activate = true
        spec = request.spec

        # check if this is one of our embedded gems
        if original_embedded_gems[spec.name]

          # check if gem can be loaded from RUBYLIB, this supports developer use case
          original_load_path.each do |lp|
            if File.exists?(File.join(lp, spec.name)) || File.exists?(File.join(lp, spec.name + '.rb')) || File.exists?(File.join(lp, spec.name + '.so'))
              $logger.debug "Found #{spec.name} in '#{lp}', overrides gem #{spec.spec_file}"
              Gem::Specification.remove_spec(spec)
              do_activate = false
              break
            end
          end
        end

        if do_activate
          $logger.debug "Activating gem #{spec.spec_file}"
          begin
            spec.activate
          rescue Gem::LoadError
            $logger.error "Error activating gem #{spec.spec_file}"
            activation_errors = true
          end
        end

      end

      if activation_errors
        return false
      end

    ensure
      Dir.chdir(current_dir)
    end

  end # use_bundler

  # Handle -e commands
  remove_indices = []
  $eval_cmds = []
  main_args.each_index do |i|

    if main_args[i] == '-e' || main_args[i] == '--execute'
      # remove from further processing
      remove_indices << i
      remove_indices << i+1

      cmd = main_args[i + 1]

      if cmd.nil?
        $logger.error "#{main_args[i]} requires second argument CMD"
        return false
      end

      $eval_cmds << cmd
    end
  end
  remove_indices.reverse_each {|i| main_args.delete_at(i)}

  if !main_args.empty?
    $logger.error "Unknown arguments #{main_args} found"
    return false
  end

  return true
end


# This CLI class processes the input args and invokes the proper command class
class CLI

  # This constant maps commands to classes in this CLI and stores meta-data on them
  def command_list
    {
        gem_list: [ Proc.new { ::GemList }, {primary: false, working: true}],
        gem_install: [ Proc.new { ::InstallGem }, {primary: false, working: false}], # DLM: needs Ruby built with FFI
        execute_ruby_script: [ Proc.new { ::ExecuteRubyScript }, {primary: false, working: true}],
        interactive_ruby: [ Proc.new { ::InteractiveRubyShell }, {primary: false, working: false}], # DLM: not working
        ruby_version: [ Proc.new { ::RubyVersion }, {primary: false, working: true}],
        list_commands: [ Proc.new { ::ListCommands }, {primary: true, working: true}]
    }
  end

  # This method instantiates the global variables $main_args, $sub_command, and $sub_args
  #
  # @param [Array] argv The arguments passed through the CLI
  # @return [Object] An instance of the CLI class with initialized globals
  #
  def initialize(argv)
    $main_args, $sub_command, $sub_args = split_main_and_subcommand(argv, command_list)

    if $main_args.include? '--verbose'
      $logger.level = Logger::DEBUG
    end

    $logger.info("CLI Parsed Inputs: #{$main_args.inspect} #{$sub_command.inspect} #{$sub_args.inspect}")
  end

  # Checks to see if it should print the main help, and if not parses the command into a class and executes it
  def execute
    $logger.debug "Main arguments are #{$main_args}"
    $logger.debug "Sub-command is #{$sub_command}"
    $logger.debug "Sub-arguments are #{$sub_args}"
    if $main_args.include?('-h') || $main_args.include?('--help')
      # Help is next in short-circuiting everything. Print
      # the help and exit.
      help
      return 0
    end

    if !parse_main_args($main_args)
      help
      return 1
    end

    # -e commands detected
    if !$eval_cmds.empty?
      $eval_cmds.each do |cmd|
        $logger.debug "Executing cmd: #{cmd}"
        eval(cmd)
      end
      if $sub_command
        $logger.warn "Evaluate mode detected, ignoring sub_command #{$sub_command}"
        return 0
      end
      return 0
    end

    # If we reached this far then we must have a command. If not,
    # then we also just print the help and exit.
    command_plugin = nil
    if $sub_command
      command_plugin = command_list[$sub_command.to_sym]
    end

    if !command_plugin || !$sub_command
      help
      return 1
    end

    command_class = command_plugin[0].call
    $logger.debug("Invoking command class: #{command_class} #{$sub_args.inspect}")

    # Initialize and execute the command class, returning the exit status.
    result = 0
    begin
      result = command_class.new.execute($sub_args)
    rescue Interrupt
      $logger.error '?'
      result = 1
    end

    result = 0 unless result.is_a?(Integer)
    result
  end

  # Prints out the help text for the CLI
  #
  # @param [Boolean] list_all If set to true, the help prints all commands, however it otherwise only prints those
  #   marked as primary in #command_list
  # @param [Boolean] quiet If set to true, list only the names of commands without the header
  # @return [void]
  # @see #command_list #::ListCommands
  #
  def help(list_all=false, quiet=false)
    if quiet
      commands = ['-h','--help',
                  '--verbose',
                  '-i', '--include',
                  '-e', '--execute',
                  '--gem_path', '--gem_home', '--bundle', '--bundle_path', '--bundle_without']
      command_list.each do |key, data|
        # Skip non-primary commands. These only show up in extended
        # help output.
        next unless data[1][:primary] unless list_all
        commands << key.to_s
      end
      safe_puts commands #.join(" ")

    else
      opts = OptionParser.new do |o|
        o.banner = 'Usage: openstudio [options] <command> [<args>]'
        o.separator ''
        o.on('-h', '--help', 'Print this help.')
        o.on('--verbose', 'Print the full log to STDOUT')
        o.on('-I', '--include DIR', 'Add additional directory to add to front of Ruby $LOAD_PATH (may be used more than once)')
        o.on('-e', '--execute CMD', 'Execute one line of script (may be used more than once). Returns after executing commands.')
        o.on('--gem_path DIR', 'Add additional directory to add to front of GEM_PATH environment variable (may be used more than once)')
        o.on('--gem_home DIR', 'Set GEM_HOME environment variable')
        o.on('--bundle GEMFILE', 'Use bundler for GEMFILE')
        o.on('--bundle_path BUNDLE_PATH', 'Use bundler installed gems in BUNDLE_PATH')
        o.on('--bundle_without WITHOUT_GROUPS', 'Space separated list of groups for bundler to exclude in WITHOUT_GROUPS.  Surround multiple groups with quotes like "test development".')
        o.separator ''
        o.separator 'Common commands:'

        # Add the available commands as separators in order to print them
        # out as well.
        commands = {}
        longest = 0
        command_list.each do |key, data|
          # Skip non-primary commands. These only show up in extended
          # help output.
          next unless data[1][:primary] unless list_all

          key           = key.to_s
          klass         = data[0].call
          commands[key] = klass.synopsis
          longest       = key.length if key.length > longest
        end

        commands.keys.sort.each do |key|
          o.separator "     #{key.ljust(longest+2)} #{commands[key]}"
        end

        o.separator ''
        o.separator 'For help on any individual command run `openstudio COMMAND -h`'
        unless list_all
          o.separator ''
          o.separator 'Additional commands are available, but are either more advanced'
          o.separator 'or not commonly used. To see all commands, run the command'
          o.separator '`openstudio list_commands`.'
        end
      end

      safe_puts opts.help
    end
  end
end

# Class to list the gems used by the CLI
class GemList

  # Provides text for the main help functionality
  def self.synopsis
    'Lists the set gems available to openstudio'
  end

  # Alters the environment variable used to define the gem install location
  #
  # @param [Array] sub_argv Options passed to the gem_install command from the user input
  # @return [Fixnum] Return status
  #
  def execute(sub_argv)
    require 'rubygems'

    $logger.info "GemList, sub_argv = #{sub_argv}"

    options = {}

    # Parse the options
    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio gem_list'
    end
    argv = parse_options(opts, sub_argv)
    return 0 if argv == nil

    $logger.debug("GemList command: #{argv.inspect} #{options.inspect}")

    unless argv == []
      $logger.error 'Extra arguments passed to the gem_list command. Please refer to the help documentation.'
      return 1
    end

    begin
      embedded = []
      user = []
      Gem::Specification.find_all.each do |spec|
        if spec.gem_dir.chars.first == ':'
          embedded << spec
        else
          user << spec
        end
      end

      embedded.each do |spec|
        safe_puts "#{spec.name} (#{spec.version}) '#{spec.gem_dir}'"
      end

      user.each do |spec|
        safe_puts "#{spec.name} (#{spec.version}) '#{spec.gem_dir}'"
      end

    rescue => e
      $logger.error "Error listing gems: #{e.message} in #{e.backtrace.join("\n")}"
      exit e.exit_code
    end

    0
  end
end

# Class to install gems using the RubyGems functionality
class InstallGem

  # Provides text for the main help functionality
  def self.synopsis
    'Installs a Gem using the embedded ruby'
  end

  # Executes the RubyGems gem install process, using the RubyGems options
  #
  # @param [Array] sub_argv Options passed to the gem_install command from the user input
  # @return [Fixnum] Return status
  #
  def execute(sub_argv)
    require 'rubygems'
    require 'rubygems/commands/install_command'

    $logger.info "InstallGem, sub_argv = #{sub_argv}"

    options = {}

    # Parse the options
    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio gem_install gem_name gem_version'
      o.separator ''
      o.separator 'Options:'
      o.separator ''
    end

    # Parse the options
    argv = parse_options(opts, sub_argv)
    return 0 if argv == nil

    $logger.debug("InstallGem command: #{argv.inspect} #{options.inspect}")

    if argv == []
      $logger.error 'No gem name provided'
      return 1
    end
    gem_name = argv[0]
    gem_version = argv[1]

    cmd = Gem::Commands::InstallCommand.new
    cmd.handle_options ["--no-ri", "--no-rdoc", 'rake', '--version', '0.9']  # or omit --version and the following option to install the latest

    ARGV.clear
    ARGV << gem_name
    if gem_version
      ARGV << '--version'
      ARGV << gem_version
    end

    $logger.info "Installing gem to #{ENV['GEM_HOME']}"

    begin
      cmd.execute
    rescue => e
      $logger.error "Error installing gem: #{e.message} in #{e.backtrace.join("\n")}"
      exit e.exit_code
    rescue LoadError => e
      # DLM: gem install tries to load a Windows dll to access network functionality in win32/resolv
      # Ruby must be built with libffi to enable fiddle extension to enable win32 extension
      $logger.error "gem_install command not yet implemented, requires fiddle extension"
      #$logger.error "#{e.message} in #{e.backtrace.join("\n")}"
      return 1
    end

    $logger.info 'The gem was successfully installed'

    0
  end
end

# Class to execute a ruby script
class ExecuteRubyScript

  # Provides text for the main help functionality
  def self.synopsis
    'Executes a ruby file'
  end

  # Executes an arbitrary ruby script
  #
  # @param [Array] sub_argv Options passed to the execute_ruby_script command from the user input
  # @return [Fixnum] Return status
  #
  def execute(sub_argv)

    $logger.info "ExecuteRubyScript, sub_argv = #{sub_argv}"

    require 'pathname'

    options = {}

    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio execute_ruby_script file [arguments]'
    end

    if sub_argv.size == 1
      if sub_argv[0] == '-h' || sub_argv[0] == '--help'
        safe_puts(opts.help)
        return 0
      end
    end

    # Parse the options
    # DLM: don't do argument parsing as in other commands since we want to pass the remaining arguments to the ruby script
    return 0 if sub_argv == nil
    return 1 unless sub_argv
    $logger.debug("ExecuteRubyScript command: #{sub_argv.inspect}")
    file_path = sub_argv.shift.to_s
    file_path = File.absolute_path(File.join(Dir.pwd, file_path)) unless Pathname.new(file_path).absolute?
    $logger.debug "Path for the file to run: #{file_path}"

    ARGV.clear
    sub_argv.each do |arg|
      ARGV << arg
    end

    $logger.debug "ARGV: #{ARGV}"

    unless File.exists? file_path
      $logger.error "Unable to find the file #{file_path} on the filesystem"
      return 1
    end

    require file_path

    0
  end
end

# Class to put the user into an irb shell
class InteractiveRubyShell

  # Provides text for the main help functionality
  def self.synopsis
    'Provides an interactive ruby shell'
  end

  # Executes the commands to get into an IRB prompt
  #
  # @param [Array] sub_argv Options passed to the interactive_ruby command from the user input
  # @return [Fixnum] Return status
  #
  def execute(sub_argv)
    require 'irb'

    $logger.info "InteractiveRubyShell, sub_argv = #{sub_argv}"

    options = {}

    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio interactive_ruby'
    end

    # Parse the options
    argv = parse_options(opts, sub_argv)
    return 0 if argv == nil

    $logger.debug("InteractiveRubyShell command: #{argv.inspect} #{options.inspect}")

    unless argv == []
      $logger.error 'Extra arguments passed to the i command.'
      return 1
    end

    IRB.start_session(binding)

    0
  end
end

# Class to return the ruby version used by the packaged CLI
class RubyVersion

  # Provides text for the main help functionality
  def self.synopsis
    'Returns the Ruby version used by the CLI'
  end

  # Evaluates the RUBY_VERSION constant and returns it
  #
  # @param [Array] sub_argv Options passed to the ruby_version command from the user input
  # @return [Fixnum] Return status
  #
  def execute(sub_argv)

    $logger.info "RubyVersion, sub_argv = #{sub_argv}"

    options = {}

    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio ruby_version'
    end

    # Parse the options
    argv = parse_options(opts, sub_argv)
    return 0 if argv == nil

    $logger.debug("RubyVersion command: #{argv.inspect} #{options.inspect}")

    unless argv == []
      $logger.error 'Arguments passed to the ruby_version command.'
      return 1
    end

    safe_puts RUBY_VERSION

    0
  end
end

# Class to return the full set of possible commands for the CLI
class ListCommands

  # Provides text for the main help functionality
  def self.synopsis
    'Lists the entire set of available commands'
  end

  # Executes the standard help method with the list_all attribute set to true
  #
  # @param [Array] sub_argv Options passed to the list_all command from the user input
  # @return [Fixnum] Return status
  # @see #::CLI.help
  #
  def execute(sub_argv)

    $logger.info "ListCommands, sub_argv = #{sub_argv}"

    options = {}

    opts = OptionParser.new do |o|
      o.banner = 'Usage: openstudio list_commands'
      o.separator ''
      o.separator 'Options:'
      o.separator ''

      o.on('--quiet', "If --quiet is passed, list only the names of commands without the header") do
        options[:quiet] = true
      end

    end

    # Parse the options
    argv = parse_options(opts, sub_argv)
    return 0 if argv == nil

    $logger.debug("ListCommands command: #{argv.inspect} #{options.inspect}")

    # If anything else than --quiet is passed
    unless argv == []
      $logger.error 'Extra Arguments passed to the list_commands command, please refer to the help documentation.'
      return 1
    end

    if options[:quiet]
      $logger.debug 'Creating a new CLI instance and calling help with list_all AND quiet enabled'
      ::CLI.new([]).help(true, true)
    else
      $logger.debug 'Creating a new CLI instance and calling help with list_all enabled'
      ::CLI.new([]).help(true)
    end
    0
  end
end


### Configure Gems to load the correct Gem files
### @see http://rubygems.rubyforge.org/rubygems-update/Gem.html

# Execute the CLI interface, and exit with the proper error code
$logger.info "Executing argv: #{ARGV}"

begin
  result = CLI.new(ARGV).execute
rescue Exception => e
  puts "Error executing argv: #{ARGV}"
  puts "Error: #{e.message} in #{e.backtrace.join("\n")}"
  result = 1
end
STDOUT.flush

if result != 0
  # DLM: exit without a call stack but with a non-zero exit code
  exit!(false)
end
