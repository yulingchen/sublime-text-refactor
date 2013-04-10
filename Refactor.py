import commands
import subprocess
import sublime
import sublime_plugin
import os
import os.path
import json
from os.path import dirname, realpath


REFACTOR_PLUGIN_FOLDER = dirname(realpath(__file__)) + "/"


class RefactorBaseClass(sublime_plugin.TextCommand):
    currentCursorPosition = -1

    def save(self):
        self.view.run_command("save")

    def executeNodeJsShell(self, cmd):
        out = ""
        err = ""
        result = ""
        if sublime.platform() == 'windows':
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
            (out, err) = p.communicate()

            if err != '':
                sublime.error_message(err)
            else:
                result = out
        else:
            # fixme: fetch error messages
            result = commands.getoutput('"'+'" "'.join(cmd)+'"')
        return result

    def applyMultipleSelections(self, selections):
        for region in selections:
            r = sublime.Region(self.currentCursorPosition + region[0], self.currentCursorPosition + region[1])
            self.view.sel().add(r)

    def abortMultiselection(self):
        if len(self.view.sel()) != 1:
            sublime.error_message("Multiple selection is not supported.")
            return True
        else:
            return False

    def openJSONFile(self, filename):
        json_file = open(filename)
        data = json.load(json_file)
        json_file.close()
        return data

    def writeTextFile(self, data, filename):
        text_file = open(filename, "w")
        text_file.write(data)
        text_file.close()

    def replaceCurrentTextSelection(self, edit, text):
        startPos = 0
        for region in self.view.sel():
            startPos = region.a
            if region.b < startPos:
                startPos = region.b
            self.view.replace(edit, region, text.decode('utf-8'))
            self.currentCursorPosition = startPos
        return startPos


class RefactorCommand(RefactorBaseClass):
    def run(self, edit):
        self.RefactorCommand(edit)

    def RefactorCommand(self, edit):
        if self.abortMultiselection():
            return

        scriptPath = REFACTOR_PLUGIN_FOLDER + "js/run.js"
        tempFile = REFACTOR_PLUGIN_FOLDER + "tmp.txt.js"
        jsonResultTempFile = REFACTOR_PLUGIN_FOLDER + "resultCodePositions.json"
        settings = ' '.join([
            "indent_size:\ 2",
            "indent_char:\ ' '",
            "max_char:\ 80",
            "brace_style:\ collapse"
        ])

        cmd = ["node", scriptPath, tempFile, settings]
        code = self.view.substr(self.view.sel()[0])
        self.writeTextFile(code, tempFile)
        refactoredText = self.executeNodeJsShell(cmd)

        if len(refactoredText):
            self.replaceCurrentTextSelection(edit, refactoredText)

            self.view.sel().clear()
            selections = self.openJSONFile(jsonResultTempFile)
            self.applyMultipleSelections(selections)

            os.remove(jsonResultTempFile)
        os.remove(tempFile)
