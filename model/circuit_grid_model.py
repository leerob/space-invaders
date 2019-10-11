#
# Copyright 2019 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import numpy as np

from qiskit import QuantumCircuit, QuantumRegister

from model import circuit_node_types as node_types
from utils.parameters import CIRCUIT_DEPTH


class CircuitGridModel:
    """Grid-based model that is built when user interacts with circuit"""
    def __init__(self, max_wires, max_columns):
        self.max_wires = max_wires
        self.max_columns = max_columns
        self.nodes = np.empty((max_wires, max_columns), dtype=CircuitGridNode)

    def __str__(self):
        retval = ''
        for wire_num in range(self.max_wires):
            retval += '\n'
            for column_num in range(self.max_columns):
                retval += str(self.get_node_gate_part(wire_num, column_num)) + ', '
        return 'CircuitGridModel: ' + retval

    def set_node(self, wire_num, column_num, circuit_grid_node):
        self.nodes[wire_num][column_num] = \
            CircuitGridNode(circuit_grid_node.node_type,
                            circuit_grid_node.radians,
                            circuit_grid_node.ctrl_a,
                            circuit_grid_node.ctrl_b,
                            circuit_grid_node.swap)

        # TODO: Decide whether to protect as shown below
        # if not self.nodes[wire_num][column_num]:
        #     self.nodes[wire_num][column_num] = CircuitGridNode(node_type, radians)
        # else:
        #     print('Node ', wire_num, column_num, ' not empty')

    def get_node(self, wire_num, column_num):
        return self.nodes[wire_num][column_num]

    def get_node_gate_part(self, wire_num, column_num):
        requested_node = self.nodes[wire_num][column_num]
        if requested_node and requested_node.node_type != node_types.EMPTY:
            # Node is occupied so return its gate
            return requested_node.node_type
        else:
            # Check for control nodes from gates in other nodes in this column
            nodes_in_column = self.nodes[:, column_num]
            for idx in range(self.max_wires):
                if idx != wire_num:
                    other_node = nodes_in_column[idx]
                    if other_node:
                        if other_node.ctrl_a == wire_num or other_node.ctrl_b == wire_num:
                            return node_types.CTRL
                        elif other_node.swap == wire_num:
                            return node_types.SWAP

        return node_types.EMPTY

    def get_gate_wire_for_control_node(self, control_wire_num, column_num):
        """Get wire for gate that belongs to a control node on the given wire"""
        gate_wire_num = -1
        nodes_in_column = self.nodes[:, column_num]
        for wire_idx in range(self.max_wires):
            if wire_idx != control_wire_num:
                other_node = nodes_in_column[wire_idx]
                if other_node:
                    if other_node.ctrl_a == control_wire_num or \
                            other_node.ctrl_b == control_wire_num:
                        gate_wire_num =  wire_idx
                        print("Found gate: ",
                              self.get_node_gate_part(gate_wire_num, column_num),
                              " on wire: " , gate_wire_num)
        return gate_wire_num

    def compute_circuit(self):
        qr = QuantumRegister(self.max_wires, 'q')
        qc = QuantumCircuit(qr)

        for column_num in range(self.max_columns):
            for wire_num in range(self.max_wires):
                node = self.nodes[wire_num][column_num]
                if node:
                    if node.node_type == node_types.IDEN:
                        # Identity gate
                        qc.iden(qr[wire_num])
                    elif node.node_type == node_types.X:
                        if node.radians == 0:
                            if node.ctrl_a != -1:
                                if node.ctrl_b != -1:
                                    # Toffoli gate
                                    qc.ccx(qr[node.ctrl_a], qr[node.ctrl_b], qr[wire_num])
                                else:
                                    # Controlled X gate
                                    qc.cx(qr[node.ctrl_a], qr[wire_num])
                            else:
                                # Pauli-X gate
                                qc.x(qr[wire_num])
                        else:
                            # Rotation around X axis
                            qc.rx(node.radians, qr[wire_num])
                    elif node.node_type == node_types.Y:
                        if node.radians == 0:
                            if node.ctrl_a != -1:
                                # Controlled Y gate
                                qc.cy(qr[node.ctrl_a], qr[wire_num])
                            else:
                                # Pauli-Y gate
                                qc.y(qr[wire_num])
                        else:
                            # Rotation around Y axis
                            qc.ry(node.radians, qr[wire_num])
                    elif node.node_type == node_types.Z:
                        if node.radians == 0:
                            if node.ctrl_a != -1:
                                # Controlled Z gate
                                qc.cz(qr[node.ctrl_a], qr[wire_num])
                            else:
                                # Pauli-Z gate
                                qc.z(qr[wire_num])
                        else:
                            if node.ctrl_a != -1:
                                # Controlled rotation around the Z axis
                                qc.crz(node.radians, qr[node.ctrl_a], qr[wire_num])
                            else:
                                # Rotation around Z axis
                                qc.rz(node.radians, qr[wire_num])
                    elif node.node_type == node_types.S:
                        # S gate
                        qc.s(qr[wire_num])
                    elif node.node_type == node_types.SDG:
                        # S dagger gate
                        qc.sdg(qr[wire_num])
                    elif node.node_type == node_types.T:
                        # T gate
                        qc.t(qr[wire_num])
                    elif node.node_type == node_types.TDG:
                        # T dagger gate
                        qc.tdg(qr[wire_num])
                    elif node.node_type == node_types.H:
                        if node.ctrl_a != -1:
                            # Controlled Hadamard
                            qc.ch(qr[node.ctrl_a], qr[wire_num])
                        else:
                            # Hadamard gate
                            qc.h(qr[wire_num])
                    elif node.node_type == node_types.SWAP:
                        if node.ctrl_a != -1:
                            # Controlled Swap
                            qc.cswap(qr[node.ctrl_a], qr[wire_num], qr[node.swap])
                        else:
                            # Swap gate
                            qc.swap(qr[wire_num], qr[node.swap])

        return qc

    def reset_circuit(self):
        self.nodes = np.empty((self.max_wires, self.max_columns),
                              dtype=CircuitGridNode)
        # the game crashes if the circuit is empty
        # initialize circuit with 3 identity gate at the end to prevent crash
        # identity gate are displayed by completely transparent PNG

        for i in range(self.max_wires):
            self.set_node(i, CIRCUIT_DEPTH - 1, CircuitGridNode(node_types.IDEN))


class CircuitGridNode:
    """Represents a node in the circuit grid"""
    def __init__(self, node_type, radians=0.0, ctrl_a=-1, ctrl_b=-1, swap=-1):
        self.node_type = node_type
        self.radians = radians
        self.ctrl_a = ctrl_a
        self.ctrl_b = ctrl_b
        self.swap = swap

    def __str__(self):
        string = 'type: ' + str(self.node_type)
        string += ', radians: ' + str(self.radians) if self.radians != 0 else ''
        string += ', ctrl_a: ' + str(self.ctrl_a) if self.ctrl_a != -1 else ''
        string += ', ctrl_b: ' + str(self.ctrl_b) if self.ctrl_b != -1 else ''
        return string
