import yaml
import os


def mac_hex(number):
    temp = hex(number)[2:]
    if number < 10:
        temp = "0{0}".format(temp)
    elif number > 99:
        raise NotImplementedError(
            "Incrementing MAC addresses only implemented up to 99.")
    else:
        pass
    return temp


def yaml_replace_line(yaml_string, line_identifier, replacement):
    for line in yaml_string.splitlines():
        if line_identifier in line:
            whitespace = len(line) - len(line.lstrip(" "))
            return yaml_string.replace(line, "{spaces}{content}".format(
                spaces=" " * whitespace,
                content=replacement
            ))


class VnfElement(object):
    def __init__(self, base_mac, base_ip, index, memif_count):
        self.vnf_index = index
        self.memifs = [
            base_mac.format(mac_hex(x + 1), mac_hex(self.vnf_index + 1))
            for x in range(memif_count)]
        self.ip_addresses = [
            base_ip.format(x + 1, self.vnf_index + 1)
            for x in range(memif_count)]


class YamlConfigGenerator(object):
    def __init__(self, vnf_count, novpp_count, memif_per_vnf, template_folder):
        self.vnf_count = int(vnf_count)
        self.novpp_count = int(novpp_count)
        self.memif_per_vnf = memif_per_vnf
        self.templates = {}
        self.output = {}
        self.load_templates(template_folder)

    def load_templates(self, template_folder):
        with open("{0}/sfc-k8.yaml".format(template_folder), "r") as sfc:
            self.templates["sfc"] = sfc.read()
        with open("{0}/vnf-vpp.yaml".format(template_folder), "r") as vnf:
            self.templates["vnf"] = vnf.read()
        with open("{0}/novpp.yaml".format(template_folder), "r") as novpp:
            self.templates["novpp"] = novpp.read()
        print self.templates

    def generate_config(self, output_path):
        self.generate_sfc_config()
        # self.generate_vnf_config()
        # self.generate_novpp_config()
        # self.write_config_files(output_path)

    def generate_sfc_config(self):

        vnf_list = []
        for index in range(self.vnf_count):
            vnf_list.append(VnfElement(
                "10.01.01.01.{0}.{1}",
                "192.168.{0}.{1}",
                index,
                self.memif_per_vnf))

        entities = []
        for bridge in range(self.memif_per_vnf):
            entity = {
                "name": "vswitch-bridge{index}".format(index=bridge),
                "description": "VSwitch L2 bridge.",
                "type": 8,
                "elements": [
                    {"container": "agent_vpp_vswitch",
                     "port_label": "L2-bridge{index}".format(index=bridge),
                     "etcd_vpp_switch_key": "agent_vpp_vswitch",
                     "l2fib_macs": [vnf_list[x].memifs[bridge]
                                    for x in range(len(vnf_list))],
                     "type": 5}
                ]}
            for vnf in vnf_list:
                vnf_element = {
                    "container": "vnf-vpp-{index}".format(index=vnf.vnf_index),
                    "port_label": "vnf{vnf_index}_memif{bridge_index}".format(
                        vnf_index=vnf.vnf_index, bridge_index=bridge),
                    "mac_addr": vnf.memifs[bridge],
                    "ipv4_addr": vnf.ip_addresses[bridge],
                    "type": 2,
                    "etcd_vpp_switch_key": "agent_vpp_vswitch"
                }
                entity["elements"].append(vnf_element)
            entities.append(entity)

        output = ""
        for line in yaml.dump(
                entities,
                default_flow_style=False
        ).splitlines():
            output += " "*6 + line + "\n"

        template = self.templates["sfc"]
        if "---" in template:
            sections = template.split("---")
            for section in sections:
                if "sfc_entities:" in section:
                    output = template.replace(section, section + output)
                    print output
                    self.output["sfc"] = output
        else:
            print self.templates["sfc"] + output

        # for vnf_index in range(self.vnf_count):
        #     new_element = {
        #         "container": "vnf-vpp-{index}".format(index=vnf_index),
        #         "port_label": "vnf{index}_memif0".format(index=vnf_index),
        #         "mac_addr": "10.01.01.01.01.{0}".format(mac_hex(vnf_index)),
        #         "ipv4_addr": "192.168.5.{0}".format(vnf_index),
        #         "type": 2,
        #         "etcd_vpp_vswitch_key": "agent_vpp_vswitch"
        #     }
        #     elements_list.append(new_element)
        # for index in range(self.vnf_count, self.vnf_count + self.novpp_count):
        #     novpp_index = index - self.vnf_count
        #     new_element = {
        #         "container": "novpp-{index}".format(index=novpp_index),
        #         "port_label": "veth_novpp{index}".format(index=novpp_index),
        #         "mac_addr": "10.01.01.01.01.{0}".format(mac_hex(index)),
        #         "ipv4_addr": "192.168.5.{0}".format(index),
        #         "type": 3,
        #         "etcd_vpp_vswitch_key": "agent_vpp_vswitch"
        #     }
        #     elements_list.append(new_element)
        #
        #     new_element = {
        #         "container": "agent_vpp_vswitch",
        #         "port_label": "L2-bridge",
        #         "l2fib_macs": ["10.01.01.01.01.{0}".format(
        #             mac_hex(x)) for x in range(len(elements_list))],
        #         "etcd_vpp_vswitch_key": "agent_vpp_vswitch"
        #     }
        #     elements_list.append(new_element)
        #
        # output = ""
        # for line in yaml.dump(
        #         elements_list,
        #         default_flow_style=False
        # ).splitlines():
        #     output += " "*8 + line + "\n"
        #
        # template = self.templates["sfc"]
        # if "---" in template:
        #     sections = template.split("---")
        #     for section in sections:
        #         if "sfc_entities:" in section:
        #             output = template.replace(section, section + output)
        #             print output
        #             self.output["sfc"] = output
        # else:
        #     print self.templates["sfc"] + output

    def generate_vnf_config(self):
        template = self.templates["vnf"]
        output = yaml_replace_line(
            template,
            "replicas:",
            "replicas: {0}".format(self.vnf_count))
        print output
        self.output["vnf"] = output

    def generate_novpp_config(self):
        template = self.templates["novpp"]
        output = yaml_replace_line(
            template,
            "replicas:",
            "replicas: {0}".format(self.novpp_count))
        print output
        self.output["novpp"] = output

    def write_config_files(self, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        with open("{0}/sfc.yaml".format(output_path), "w") as sfc:
            sfc.write(self.output["sfc"])
        with open("{0}/vnf.yaml".format(output_path), "w") as vnf:
            vnf.write(self.output["vnf"])
        with open("{0}/novpp.yaml".format(output_path), "w") as novpp:
            novpp.write(self.output["novpp"])


def generate_config(vnf_count, novpp_count, memif_per_vnf, template_path, output_path):
    generator = YamlConfigGenerator(
        vnf_count,
        novpp_count,
        memif_per_vnf,
        template_path)
    generator.generate_config(output_path)


generate_config(
    3, 3, 6,
    "/home/sam/git/vpp-agent-selias/tests/robot/resources/k8-yaml", ".")
