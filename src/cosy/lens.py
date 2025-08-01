"""
Jacob Gobbo
Lanzara Group - UC Berkeley
2021/2022

low level info -
coefE:       information about each piece of elecrtrodes
coefE(i,1):  number of points
coefE(i,2):  type, 1 for line, 2 for arc
coefE(i,3):  voltage
coefE(i,4):  starting point in z if type is 1, starting angle (degree) if type is 2
coefE(i,5):  starting point in r if type is 1, 0 if type is 2
coefE(i,6):  ending point in z if type is 1, ending angle (degree) if type is 2
coefE(i,7):  ending point in r if type is 1, 0 if type is 2
coefE(i,8):  0 if type is 1, R if type is 2 ( (r-r0)^2+(z-z0)^2=R^2 )
coefE(i,9):  0 if type is 1, z0 if type is 2
coefE(i,10): 0 if type is 1, r0 if type is 2

coefR is the same except coefR(i,3) = 0
"""

from dataclasses import dataclass, field
from math import sqrt, ceil, atan2, degrees, radians, sin, cos, tan
from pathlib import Path
from copy import deepcopy


@dataclass
class Lens:
    INSTRUCTIONS = """
        Instructions:

        1. Initialize a Lens.
        2. Set a starting point for an electrode. (for automated electrode grouping, specify voltage_group)
        3. Draw a line to the next point using Lens.line(end_x, end_y) (method chaining supported).
        4. Draw lines or arcs until the end of a particular electrode.
            Make sure to go counterclockwise so that the ring offsets are calculated properly.
        5. Finish an electrode by calling Lens.count_pieces(electrode_name)
        6. Repeat steps 3, 4, and 5 for the rest of the electrodes

        Notes:

        horizontal and vertical lines can be added more easily by just specifying the
        ending z/r with the .horizontal()/.vertical() methods

        the ending direction for an arc is defined w.r.t. the z axis (-180, 180)

        arcs > 180deg aren't supported, 180 degree arcs are always counterclockwise i.e. inside
        arcs > 180deg could probably be made by chaining arcs together (haven't tested this)
        """

    point_spacing: float = 0.1
    er_spacing: float = None  # spacing between electrodes and rings

    z_start: float = 0
    z_offset: float = 0
    r_start: float = 0
    start_direction: float = None
    prev_piece: str = None
    voltage: int = -1

    coefE: list = field(default_factory=list)
    coefR: list = field(default_factory=list)

    n_pieces: dict = field(default_factory=dict)
    nTotal: int = 0

    def __post_init__(self):
        # er_spacing should nominally be set to the point_spacing
        self.er_spacing = (
            self.er_spacing if self.er_spacing is not None else self.point_spacing
        )

    def start(self, z: float, r: float, *, voltage_group: int = None):
        self.voltage = voltage_group if voltage_group is not None else self.voltage + 1

        self.z_start = z
        self.r_start = r
        self.start_direction = None

        self.prev_piece = "start"

        return self

    def line(self, z_end: float, r_end: float):
        if z_end == self.z_start and r_end == self.r_start:
            raise ValueError("Your lines have to go somewhere.")
        length = sqrt((z_end - self.z_start) ** 2 + (r_end - self.r_start) ** 2)
        n_points = ceil(length / self.point_spacing)

        coefR_z_start, coefR_z_end = self._calc_z_shift(z_end, r_end, length)
        coefR_r_start, coefR_r_end = self._calc_r_shift(z_end, r_end, length)

        self.coefE.append(
            [
                n_points,
                1,
                self.voltage,
                self.z_start + self.z_offset,
                self.r_start,
                z_end + self.z_offset,
                r_end,
                0,
                0,
                0,
            ]
        )
        self.coefR.append(
            [
                n_points,
                1,
                0,
                coefR_z_start + self.z_offset,
                coefR_r_start,
                coefR_z_end + self.z_offset,
                coefR_r_end,
                0,
                0,
                0,
            ]
        )

        if self.prev_piece == "line":
            self._corner_correction(z_end, r_end)

        if self.start_direction is None:
            new_ang = atan2(r_end - self.r_start, z_end - self.z_start)
            self.start_direction = degrees(new_ang)

        self.z_start = z_end
        self.r_start = r_end

        self.prev_piece = "line"

        return self

    def vertical(self, end_r: float):
        if end_r == self.r_start:
            raise ValueError("Verticals can't end at the starting r.")
        self.line(self.z_start, end_r)

        return self

    def horizontal(self, end_z: float):
        if end_z == self.z_start:
            raise ValueError("Horizontals can't end at the starting z.")
        self.line(end_z, self.r_start)

        return self

    def _calc_z_shift(self, end_z: float, end_r: float, length: float):
        sin_theta = (end_r - self.r_start) / length
        dz = -self.er_spacing * sin_theta
        coefR_start_z = self.z_start + dz
        coefR_end_z = end_z + dz

        return coefR_start_z, coefR_end_z

    def _calc_r_shift(self, end_z: float, end_r: float, length: float):
        cos_theta = (end_z - self.z_start) / length
        dr = self.er_spacing * cos_theta
        coefR_start_r = self.r_start + dr
        coefR_end_r = end_r + dr

        return coefR_start_r, coefR_end_r

    def _corner_correction(self, end_z: float, end_r: float):
        curr_direction = degrees(atan2(end_r - self.r_start, end_z - self.z_start))
        l = round(
            self.er_spacing * tan(radians((self.start_direction - curr_direction) / 2)),
            15,
        )

        # correcting the end of the previous piece
        self.coefR[-2][5] += l * cos(radians(self.start_direction))
        self.coefR[-2][6] += l * sin(radians(self.start_direction))

        # correcting the start of the current piece
        self.coefR[-1][3] -= l * cos(radians(curr_direction))
        self.coefR[-1][4] -= l * sin(radians(curr_direction))

        self.start_direction = curr_direction

    def arc(self, end_direction: float, radius: float):
        if self.start_direction == None:
            raise ValueError(
                "There's no starting direction stored, likely because the electrode "
                "was just started. You need to draw a line before drawing an arc. "
                "Alternatively, you can set the starting direction manually before "
                "calling this."
            )

        # weird stuff can happen at the discontinuity
        if abs(self.start_direction) == 180:
            self.start_direction = -180 if end_direction < 0 else 180
        elif abs(end_direction) == 180:
            end_direction = -180 if self.start_direction < 0 else 180

        cw_dist = self.start_direction - end_direction
        ccw_dist = end_direction - self.start_direction

        if cw_dist < 0:
            cw_dist += 360
        else:
            ccw_dist += 360

        is_clockwise = cw_dist < ccw_dist

        length = radius * radians(min(cw_dist, ccw_dist))
        n_points: int = ceil(length / self.point_spacing)

        if is_clockwise:
            center_z = self.z_start + radius * sin(radians(self.start_direction))
            center_r = self.r_start - radius * cos(radians(self.start_direction))
            start_angle = self.start_direction + 90
            end_angle = end_direction + 90
        else:
            center_z = self.z_start - radius * sin(radians(self.start_direction))
            center_r = self.r_start + radius * cos(radians(self.start_direction))
            start_angle = self.start_direction - 90
            end_angle = end_direction - 90

        end_z = round(center_z + radius * cos(radians(end_angle)), 8)
        end_r = round(center_r + radius * sin(radians(end_angle)), 8)

        self.coefE.append(
            [
                n_points,
                2,
                self.voltage,
                start_angle,
                0,
                end_angle,
                0,
                radius,
                center_z + self.z_offset,
                center_r,
            ]
        )
        self.coefR.append(
            [
                n_points,
                2,
                0,
                start_angle,
                0,
                end_angle,
                0,
                (
                    (radius + self.er_spacing)
                    if is_clockwise
                    else (radius - self.er_spacing)
                ),
                center_z + self.z_offset,
                center_r,
            ]
        )

        self.z_start = end_z
        self.r_start = end_r
        self.start_direction = end_direction
        self.prev_piece = "arc"

        return self

    def count_pieces(self, name: str):
        """
        This function is only necessary for verification or if you
        want to manually define the pieces in COSY. Defining the voltage
        group at the start of each piece is a much easier method to
        automatically define pieces in COSY.
        """
        n_total = len(self.coefR)
        n_prev = sum(self.n_pieces.values())
        self.n_pieces[name] = n_total - n_prev

        return self

    def mirror(
        self, pieces_i: list[int], mirror_z: float = 0, voltage_group: int = None
    ):
        pieces_E = deepcopy([self.coefE[i] for i in pieces_i])
        pieces_R = deepcopy([self.coefR[i] for i in pieces_i])

        for piece_E, piece_R in zip(pieces_E, pieces_R):
            piece_E[2] = -piece_E[2] if voltage_group is None else voltage_group
            if piece_E[1] == 1:
                piece_type = "line"
            elif piece_E[1] == 2:
                piece_type = "arc"
            else:
                raise ValueError(
                    f"{piece_E} in your coefE list has a nonsense type. This should never happen so something is very broken."
                )

            if piece_type == "line":
                piece_E = self._mirror_line(piece_E, mirror_z)
                piece_R = self._mirror_line(piece_R, mirror_z)
            else:
                piece_E = self._mirror_arc(piece_E, mirror_z)
                piece_R = self._mirror_arc(piece_R, mirror_z)

            self.coefE.append(piece_E)
            self.coefR.append(piece_R)

        return self

    def mirror_voltage_group(self, mirror_z: float):
        pieces_i = [i for i, piece in enumerate(self.coefE) if piece[2] == self.voltage]
        self.mirror(pieces_i, mirror_z=mirror_z)

        return self

    @staticmethod
    def _mirror_coord(coord: float, mirror_point: float) -> float:
        return 2 * mirror_point - coord

    @staticmethod
    def _mirror_angle(angle: float) -> float:
        if angle < 0:
            return -180 - angle
        return 180 - angle

    @staticmethod
    def _mirror_line(piece: list, mirror_z: float) -> list:
        z_start_i = 3
        z_end_i = 5
        for i in [z_start_i, z_end_i]:
            piece[i] = Lens._mirror_coord(piece[i], mirror_z)
        return piece

    @staticmethod
    def _mirror_arc(piece: list, mirror_z: float) -> list:
        center_z_i = 8
        angle_start_i = 3
        angle_end_i = 5

        mirrored_start = Lens._mirror_angle(piece[angle_start_i])
        mirrored_end = Lens._mirror_angle(piece[angle_end_i])
        if (mirrored_start == 180) and (mirrored_end < 0):
            mirrored_start = -180
        elif (mirrored_end == 180) and (mirrored_start < 0):
            mirrored_end = -180

        piece[center_z_i] = Lens._mirror_coord(piece[center_z_i], mirror_z)
        piece[angle_start_i] = mirrored_start
        piece[angle_end_i] = mirrored_end
        return piece

    def check(self):
        for piece in self.coefR:
            self.nTotal += piece[0]

        nElec = 0
        for piece in self.coefE:
            nElec += piece[0]

        if nElec != self.nTotal:
            raise Exception(
                "Something is broken. The number of electrodes doesn't match the number of rings."
            )

    def print(self, root, printR=False, printE=False):
        self.check()

        with open(root / Path("coefR.txt"), "w") as f:
            f.write(f"{len(self.coefR)}\n")
            f.write(f"{self.nTotal}\n")

            for piece in self.coefR:
                string = f"{piece[0]:3d} {piece[1]:1d} {piece[2]:1d} {piece[3]:+1.15e} {piece[4]:+1.15e} {piece[5]:+1.15e} {piece[6]:+1.15e} {piece[7]:+1.15e} {piece[8]:+1.15e} {piece[9]:+1.15e}\n"
                f.write(string)
                if printR:
                    print(string)

        with open(root / Path("coefE.txt"), "w") as f:
            f.write(f"{len(self.coefE)}\n")

            for piece in self.coefE:
                string = f"{piece[0]:3d} {piece[1]:1d}  {piece[2]:6d}  {piece[3]:+1.14e}  {piece[4]:+1.14e}  {piece[5]:+1.14e}  {piece[6]:+1.14e}  {piece[7]:+1.14e}  {piece[8]:+1.14e}  {piece[9]:+1.14e}\n"
                f.write(string)
                if printE:
                    print(string)

        print(f"nTotal = {self.nTotal}")
        print(self.n_pieces)
