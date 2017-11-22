*** Settings ***

Library      OperatingSystem
#Library      String

Resource     ../../../variables/${VARIABLES}_variables.robot

Resource     ../../../libraries/all_libs.robot
Resource     ../../../libraries/pretty_keywords.robot

Suite Setup       Testsuite Setup
Suite Teardown    Testsuite Teardown

*** Variables ***
${VARIABLES}=          common
${ENV}=                common

*** Test Cases ***

Configure Environment
    [Tags]    setup
    Configure Environment 2
    Sleep    ${SYNC_SLEEP}
    Show Interfaces And Other Objects


Create Memifs And Loopback InterfacesOn VPP
    Create loopback interface bvi_loop0 on agent_vpp_1 with ip 10.1.1.1/24 and mac 8a:f1:be:90:00:00
    #Create loopback interface bvi_loop0 on agent_vpp_2 with ip 10.1.1.2/24 and mac 8a:f1:be:90:00:02
    Create Master memif0 on agent_vpp_1 with MAC 02:f1:be:90:00:00, key 1 and m0.sock socket
    #Create Slave memif0 on agent_vpp_2 with MAC 02:f1:be:90:00:02, key 1 and m0.sock socket
    #Create Bridge Domain bd1 With Autolearn On agent_vpp_2 with interfaces bvi_loop0, memif0
    Create Master memif1 on agent_vpp_1 with MAC 02:f1:be:90:02:00, key 2 and m1.sock socket

Create BD on VPP
    Create Bridge Domain bd1 With Autolearn On agent_vpp_1 with interfaces bvi_loop0, memif0, memif1
    Sleep    ${SYNC_SLEEP}
    Show Interfaces And Other Objects

Create Memif on Agent1

Create Memif on Agent1


    Ping from agent_vpp_1 to 10.1.1.2
    Ping from agent_vpp_2 to 10.1.1.1


