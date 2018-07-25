# coding:utf-8
# (c) 2015-2018, Wang Zhe <azrael-ex@139.com>, Zhang Qi Chuan <zhangqc@fits.com.cn>
#
# This file is part of Ansible
#
# Forward is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Forward is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
-----Introduction-----
[Core][forward] Base device class for huawei basic device method, by using paramiko module.
"""

import re
from forward.devclass.baseSSHV2 import BASESSHV2
from forward.utils.forwardError import ForwardError


class BASEHUAWEI(BASESSHV2):
    """This is a manufacturer of huawei, using the
    SSHV2 version of the protocol, so it is integrated with BASESSHV2 library.
    """
    def commit(self):
        result = {
            "status": False,
            "content": "",
            "errLog": ""
        }
        # Switch to privilege-mode.
        tmp = self.generalMode()
        if not tmp["status"]:
            # Switch failure.
            return tmp
        # Excute a command.
        tmp = self.command("save",
                           prompt={"success": "Are you sure to continue\?\[Y/N\] ?$",
                                   "error": "Error:Incomplete command[\s\S]+"})
        if tmp["state"] == "success":
            continueCommandResult = self.command("Y", prompt={"success": "successfully[\s\S]+[\r\n]+\S+> ?$"})
            if continueCommandResult["state"] == "success":
                # Successfully.
                result["status"] = True
            else:
                # Failed.
                result["errLog"] = "Failed save configuration,\
                                   relate-information: [{content}]".format(content=continueCommandResult["content"])
                result["status"] = False
        elif tmp["state"] == "error":
            result["errLog"] = "The command failed to execute.info: [{content}]".format(content=tmp["content"])
        else:
            result["errLog"] = "Failed save configuration, \
                               Info: [{content}] , [{errLog}]".format(content=tmp["content"], errLog=tmp["errLog"])
            result["content"] = "The configuration was saved successfully."
            result["status"] = True
        return result

    def generalMode(self):
        result = {
            "status": False,
            "content": "",
            "errLog": ""
        }
        # Get the current position before switch to general mode.
        # Demotion,If device currently mode-level greater than 2, It only need to execute `end`.
        if self.mode > 1:
            tmp = self.command("return", prompt={"success": "[\r\n]+\S+> ?$"})
            if tmp["state"] == "success":
                result["status"] = True
                self.mode = 1
                return result
            else:
                return tmp
        else:
            result["status"] = True
            return result

    def privilegeMode(self):
        # Switch to privilege mode.
        result = {
            "status": False,
            "content": "",
            "errLog": ""
        }
        # Get the current position Before switch to privileged mode.
        # Demotion,If device currently mode-level greater than 2, It only need to execute `end`.
        if self.mode > 2:
            toGeneralModeResult = self.generalMode()
            if toGeneralModeResult["status"] is False:
                result["errLog"] = "Demoted from hight-mode to general-mode failed."
                return result
            # else,go into privilege-mode.
        elif self.mode == 2:
            # The device is currently in privilege-mode ,so there is no required to switch.
            result["status"] = True
            return result
        # else, command line of the device is in general-mode.
        # Start switching to privilege-mode.
        sendEnableResult = self.command("system-view", prompt={"success": "[\r\n]+\S+\] ?$", "error": "[\r\n]+\S+> ?$"})
        if sendEnableResult["state"] == "success":
            # The device not required a password,thus switch is successful.
            result["status"] = True
            self.mode = 2
            return result
        elif sendEnableResult["state"] == "error":
            result["errLog"] = "Failed to switch to privilege mode, \
                               related information: [{errLog}],[{content}]".format(errLog=sendEnableResult["errLog"],
                                                                                   content=sendEnableResult["content"])
            return result
        else:
            return sendEnableResult

    def showLog(self):
        njInfo = {
            'status': False,
            'content': "",
            'errLog': ''
        }
        cmd = "display current-configuration | i log"
        prompt = {
            "success": "loghost[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.findall("loghost ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
                             result["content"], flags=re.IGNORECASE)
            if tmp:
                njInfo["content"] = tmp
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showVersion(self):
        njInfo = {
            'status': False,
            'content': "",
            'errLog': ''
        }
        cmd = "dis version"
        prompt = {
            "success": "[sS]oftware[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.search("software.*version(.*)", result["content"], flags=re.IGNORECASE)
            if tmp:
                njInfo["content"] = tmp.group(1).strip()
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showNtp(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "dis current-configuration | i ntp"
        prompt = {
            "success": "ntp-service[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.findall("ntp-service unicast-server ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})",
                             result["content"])
            if tmp:
                njInfo["content"] = tmp
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showSnmp(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "dis current-configuration | i snmp"
        prompt = {
            "success": "snmp-agent[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.findall("udp-domain ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", result["content"])
            if tmp:
                njInfo["content"] = tmp
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showVlan(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "display  vlan"
        prompt = {
            "success": "VID  Status[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            currentSection = "vlanName"
            isContinueLine = False
            for _vlanInfo in result["content"].split("\r\n"):
                if re.search("\-\-\-\-", _vlanInfo):
                    continue
                if re.search("^[0-9]", _vlanInfo) and currentSection == "vlanName":
                    isContinueLine = True
                    # Get the line of vlan.
                    lineInfo = {
                        "id": "",
                        "description": "",
                        "status": "",
                        "interface": [],
                        "type": "",
                    }
                    tmp = re.search("([0-9]+)\s+(\S+)[\s\S]+:(.*)", _vlanInfo)
                    if tmp:
                        lineInfo["id"] = tmp.group(1)
                        lineInfo["type"] = tmp.group(2)
                        if tmp.lastindex == 3:
                            lineInfo["interface"] = tmp.group(3).split()
                        njInfo["content"].append(lineInfo)
                elif isContinueLine is True and not re.search("VID  Status",
                                                              _vlanInfo) and currentSection == "vlanName":
                    for _interface in _vlanInfo.split():
                        lineInfo = njInfo["content"].pop()
                        lineInfo["interface"].append(_interface.strip())
                        njInfo["content"].append(lineInfo)
                    continue
                else:
                    isContinueLine = False
                if re.search("VID  Status", _vlanInfo):
                    currentSection = "vlanType"
                    continue
                if currentSection == "vlanType":
                    if re.search("^[0-9]", _vlanInfo.strip()):
                        tmp = re.search("([0-9]+)[ \t]+([a-z]+).*", _vlanInfo)
                        if tmp:
                            vlanID = tmp.group(1)
                            vlanStatus = tmp.group(2)
                            vlanDescription = tmp.group().split()[-1].strip()
                            i = 0
                            for _vlan in njInfo["content"]:
                                if vlanID == _vlan["id"]:
                                    njInfo["content"][i]["status"] = vlanStatus
                                    njInfo["content"][i]["description"] = vlanDescription
                                i += 1

            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showRoute(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "display  ip routing-table"
        prompt = {
            "success": "Routing[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            for _interfaceInfo in result["content"].split("\r\n"):
                # record the route table.
                lineInfo = {"net": "",
                            "mask": "",
                            "metric": "",
                            "via": [{"type": "", "via": "", "interface": ""}]}
                tmp = re.search("([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/([0-9]{1,2})\s+(\S+)\s+\
                                 \S+\s+\S+\s+\S+\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\s+(\S+)", _interfaceInfo)
                if tmp:
                    lineInfo["net"] = tmp.group(1)
                    lineInfo["mask"] = tmp.group(2)
                    lineInfo["via"][0]["type"] = tmp.group(3)
                    lineInfo["via"][0]["via"] = tmp.group(4)
                    lineInfo["via"][0]["interface"] = tmp.group(5)
                    njInfo["content"].append(lineInfo)
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showInterface(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "display interface"
        prompt = {
            "success": "Output[\s\S]+[\r\n]+\S+(>|\]) ?$",
            "error": "Unrecognized command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            interfacesFullInfo = re.findall(".*current state[\s\S]+?Output bandwidth utilization :.*",
                                            result["content"])
            for _interfaceInfo in interfacesFullInfo:
                lineInfo = {"members": [], "adminState": ""}
                # Get name of the interface.
                lineInfo['interfaceName'] = re.search("(.*) current state", _interfaceInfo).group(1)
                # Get state of the interface and remove extra character.
                lineInfo['interfaceState'] = re.search("current state : (.*)", _interfaceInfo).group(1).strip()
                # Get state of line protocol of the interface and remove extra character.
                lineInfo['lineState'] = re.search("Line protocol current state : (.*)", _interfaceInfo).group(1).strip()
                # Get description of the interface.
                lineInfo['description'] = re.search("Description:(.*)", _interfaceInfo).group(1).strip()
                # Get MUT of the interface.
                tmpMTU = re.search("The Maximum Transmit Unit is ([0-9]+)", _interfaceInfo)
                if tmpMTU:
                    lineInfo["mtu"] = tmpMTU.group(1)
                else:
                    lineInfo["mtu"] = ""
                # Get speed of the interface.
                tmp = re.search("Speed : ([0-9]+)", _interfaceInfo)
                if tmp:
                    lineInfo["speed"] = int(tmp.group(1))
                else:
                    lineInfo["speed"] = ""
                # Get duplex of the interface.
                tmp = re.search("Duplex: ([A-Z]+)", _interfaceInfo)
                if tmp:
                    lineInfo["duplex"] = tmp.group(1)
                else:
                    lineInfo["duplex"] = ""
                # Get ip of the interface.
                tmp = re.search("Internet Address is (.*)", _interfaceInfo)
                if tmp:
                    lineInfo["ip"] = tmp.group(1).split("/")[0]
                else:
                    lineInfo["ip"] = ""
                # Get mac of the interface.
                tmpMAC = re.search("Hardware address is (.*)", _interfaceInfo)
                if tmpMAC:
                    lineInfo["mac"] = tmpMAC.group(1).strip()
                else:
                    lineInfo["mac"] = ""
                # Get port type of the interface.
                tmpPortType = re.search("Physical is (.*)", _interfaceInfo)
                if tmpPortType:
                    lineInfo["type"] = tmpPortType.group(1).strip()
                else:
                    lineInfo["type"] = ""
                # Last physical down time
                tmpDownTime = re.search("Last physical down time : (.*)", _interfaceInfo)
                if tmpDownTime:
                    lineInfo["downTime"] = tmpDownTime.group(1).strip()
                else:
                    lineInfo["downTime"] = ""
                # Last physical up time
                tmpUpTime = re.search("Last physical up time : (.*)", _interfaceInfo)
                if tmpUpTime:
                    lineInfo["upTime"] = tmpUpTime.group(1).strip()
                else:
                    lineInfo["upTime"] = ""
                # Last 300 seconds input rate
                tmp = re.search("Last 300 seconds input rate (.*)", _interfaceInfo)
                if tmp:
                    lineInfo["inputRate"] = tmp.group(1)
                else:
                    lineInfo["inputRate"] = ""
                tmp = re.search("Last 300 seconds output rate (.*)", _interfaceInfo)
                if tmp:
                    lineInfo["outputRate"] = tmp.group(1)
                else:
                    lineInfo["outputRate"] = ""
                # CRC:
                tmp = re.search("CRC:.*([0-9]+)", _interfaceInfo)
                if tmp:
                    lineInfo["crc"] = tmp.group(1)
                else:
                    lineInfo["crc"] = ""
                njInfo["content"].append(lineInfo)
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def _commit(self, saveCommand='save', exitCommand='return'):
        """To save the configuration information of the device,
        it should be confirmed that the device is under the Config Mode before use.
        """
        result = {
            "status": False,
            "content": "",
            "errLog": ""
        }
        try:
            if self.isConfigMode:
                # Exit from configuration mode to privileged mode.
                self._exitConfigMode(exitCommand)
                # save setup to system
                self.shell.send('%s\n' % (saveCommand))
                while not re.search(self.prompt, result['content'].split('\n')[-1]):
                    result['content'] += self.shell.recv(1024)
                    # When prompted, reply Y,Search range at last line
                    if re.search(re.escape("Are you sure to continue?[Y/N]"), result["content"].split("\n")[-1]):
                        self.shell.send("Y\n")
                """
                If the program finds information like ‘success’, ‘OK’, ‘copy complete’, etc.
                in the received information, it indicates that the save configuration is successful.
                """
                if re.search('(\[OK\])|(Copy complete)|(successfully)', result['content'], flags=re.IGNORECASE):
                    result['status'] = True
            else:
                raise ForwardError('[Commit Config Error]: The current state is not configuration mode')
        except ForwardError, e:
            result['errLog'] = str(e)
            result['status'] = False
        return result
