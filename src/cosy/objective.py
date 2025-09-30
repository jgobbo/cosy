"""A collection of standard objective functions and associated logic to use in electron
optics optimizations with COSY
"""

from dataclasses import dataclass


@dataclass
class ObjectiveFunction:
    call: str
    endpoint: str
    function: list[str]

    def as_json(self) -> list[str]:
        return [
            f"name = {self.call}",
            f"endpoint={self.endpoint}",
        ] + self.function

    # not tested
    def __mul__(self, value: float | int) -> "ObjectiveFunction":
        return ObjectiveFunction(f"{self.call}*{value}", self.endpoint, self.function)

    def __rmul__(self, value: float | int) -> "ObjectiveFunction":
        return self.__mul__(value)

    # Not tested
    def __add__(self, other: "ObjectiveFunction") -> "ObjectiveFunction":
        assert isinstance(other, ObjectiveFunction)
        assert (
            self.endpoint == other.endpoint
        ), "Can only add ObjectiveFunctions with identical endpoints"
        return ObjectiveFunction(
            f"({self.call} + {other.call})",
            self.endpoint,
            self.function + other.function,
        )

    # not tested
    def __truediv__(self, value: float | int) -> "ObjectiveFunction":
        return ObjectiveFunction(f"{self.call}/{value}", self.endpoint, self.function)


def add_to_function(function_name: str, remainder: str) -> str:
    return f"{function_name}:={function_name}+{remainder}"


def create_function(function_name: str, remainder: list[str]) -> list[str]:
    return [f"Function {function_name} void"] + remainder + ["EndFunction"]


def mixed_third_degree_aberrations(
    function_name: str,
) -> str:
    return add_to_function(function_name, "MA(1,112)^2+MA(1,122)^2")


def free_angle_resolved_function(
    function_name: str,
) -> list[str]:
    return [
        mixed_third_degree_aberrations(function_name),
        add_to_function(function_name, "MA(1,1)^2+MA(1,111)^2+(MA(1,222)^2)/100"),
    ]


def free_spatial_resolved_function(
    function_name: str,
) -> list[str]:
    return [
        mixed_third_degree_aberrations(function_name),
        add_to_function(function_name, "MA(1,2)^2+MA(1,222)^2+(MA(1,111)^2)/100"),
    ]


def angle_resolved_function(image_diameter_mm: str, function_name: str):
    return free_angle_resolved_function(function_name) + [
        add_to_function(function_name, f"((ABS(MA(1,2))-{image_diameter_mm}/2)^2)/100")
    ]


def spatial_resolved_function(image_diameter_mm: str, function_name: str):
    return free_spatial_resolved_function(function_name) + [
        add_to_function(function_name, f"((ABS(MA(1,1))-{image_diameter_mm}/2)^2)/100")
    ]


def angle_resolved_objective_function(
    endpoint: str, image_diameter_mm: str, function_name: str = "AngleResolvedObj"
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name, angle_resolved_function(image_diameter_mm, function_name)
        ),
    )


def spatial_resolved_objective_function(
    endpoint: str, image_diameter_mm: str, function_name: str = "SpatialResolvedObj"
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name, spatial_resolved_function(image_diameter_mm, function_name)
        ),
    )


def minned_angle_resolved_objective_function(
    endpoint: str,
    min_image_d_mm: str | int | float,
    function_name: str = "MinnedAngleResolvedObj",
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            [f"If ABS(MA(1,2))<({min_image_d_mm}/2)"]
            + angle_resolved_function(min_image_d_mm, function_name)
            + ["ElseIf LO(1)"]
            + free_angle_resolved_function(function_name)
            + ["EndIf"],
        ),
    )


def maxed_angle_resolved_objective_function(
    endpoint: str,
    min_image_d_mm: str | int | float,
    function_name: str = "MinnedAngleResolvedObj",
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            [f"If ABS(MA(1,2))>({min_image_d_mm}/2)"]
            + angle_resolved_function(min_image_d_mm, function_name)
            + ["ElseIf LO(1)"]
            + free_angle_resolved_function(function_name)
            + ["EndIf"],
        ),
    )


def minned_spatial_resolved_objective_function(
    endpoint: str,
    min_image_d_mm: str | int | float,
    function_name: str = "MinnedSpatialResolvedObj",
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            [f"If ABS(MA(1,1))<({min_image_d_mm}/2)"]
            + spatial_resolved_function(min_image_d_mm, function_name)
            + ["ElseIf LO(1)"]
            + free_spatial_resolved_function(function_name)
            + ["EndIf"],
        ),
    )


def angle_filter_objective_function(
    endpoint: str,
    min_image_d_mm: str | int | float,
    function_name: str = "AngleFilterObj",
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            [f"If ABS(MA(1,2))<({min_image_d_mm}/2)"]
            + [
                add_to_function(
                    function_name, f"((ABS(MA(1,2))-{min_image_d_mm}/2)^2)/100"
                )
            ]
            + ["EndIf"]
            + [f"If ABS(MA(1,1))>(ABS(MA(1,2))/2)"]
            + [add_to_function(function_name, f"((ABS(MA(1,1))-ABS(MA(1,2))/2)^2)/100")]
            + ["EndIf"]
            + [mixed_third_degree_aberrations(function_name)]
            + [add_to_function(function_name, "MA(1,111)^2+(MA(1,222)^2)/100")],
        ),
    )


def spatial_filter_objective_function(
    endpoint: str,
    min_image_d_mm: str | int | float,
    function_name: str = "SpatialFilterObj",
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            [f"If ABS(MA(1,1))<({min_image_d_mm}/2)"]
            + [
                add_to_function(
                    function_name, f"(ABS(MA(1,1))-{min_image_d_mm}/2)^2 * 100"
                )
            ]
            + ["EndIf"]
            + [f"If ABS(MA(1,2))>({min_image_d_mm}/2)"]
            + [add_to_function(function_name, f"(ABS(MA(1,2)))^2 * 100")]
            + ["ElseIf True"]
            + [add_to_function(function_name, f"(ABS(MA(1,2)))^2")]
            + ["EndIf"]
            + [mixed_third_degree_aberrations(function_name)]
            + [add_to_function(function_name, "MA(1,111)^2 / 100 + (MA(1,222)^2)")],
        ),
    )


def clear_aperture_objective_function(
    endpoint: str, aper_d: str | int | float, function_name: str = "ClearApertureObj"
):
    return ObjectiveFunction(
        f"{function_name}(none)",
        endpoint,
        create_function(
            function_name,
            ["Variable iter 1; Variable startingR 1; Variable ii 1; Variable nAngs 1"]
            + ["Variable ri 12 6; Variable ro 12 6"]
            + [f"nAngs:=10; startingR:=0; {function_name}:=0"]
            + ["Loop iter 1 2"]
            + ["Loop ii 1 10"]
            + ["ri(1):=startingR"]
            + ["ri(2):=Sin(ii/nAngs*intAng/2)"]
            + ["ri(3):=0"]
            + ["ri(4):=0"]
            + ["ri(5):=0"]
            + ["ri(6):=0"]
            + ["Polval 1 MAP 6 ri 6 ro 6"]
            + [f"If ABS(ro(1))>({aper_d}/2)"]
            + [add_to_function(function_name, f"(ABS(ro(1))-{aper_d}/2)")]
            + ["EndIf"]
            + ["EndLoop"]
            + ["startingR:=spotSize/2"]
            + ["EndLoop"],
        ),
    )


@dataclass
class StandardObjectiveFunction:
    """
    Standard objectives for SPEEM optimization
    """

    ANGLE_RESOLVED_DETECTOR = angle_resolved_objective_function("detZ", "detD")
    SPATIAL_RESOLVED_DETECTOR = spatial_resolved_objective_function("detZ", "detD")
    MINNED_ANGLE_RESOLVED_APERTURE_0 = minned_angle_resolved_objective_function(
        "aper0Z", "aper0D"
    )
    MINNED_ANGLE_RESOLVED_DETECTOR = minned_angle_resolved_objective_function(
        "detZ", "detD"
    )
    MAXED_ANGLE_RESOLVED_DETECTOR = maxed_angle_resolved_objective_function(
        "detZ", "detD"
    )
    MAXED_ANGLE_RESOLVED_APERTURE_0 = maxed_angle_resolved_objective_function(
        "detZ", "detD"
    )
    MINNED_SPATIAL_RESOLVED_DETECTOR = minned_spatial_resolved_objective_function(
        "detZ", "detD"
    )
    ANGLE_FILTER_APERTURE_0 = angle_filter_objective_function("aper0Z", "aper0D")
    SPATIAL_FILTER_APERTURE_0 = spatial_filter_objective_function("aper0Z", "aper0D")
    ANGLE_RESOLVED_APERTURE_0 = angle_resolved_objective_function("aper0Z", "aper0D")
    MINNED_SPATIAL_RESOLVED_APERTURE_0 = minned_spatial_resolved_objective_function(
        "aper0Z", "aper0D"
    )
    CLEAR_APERTURE_0 = clear_aperture_objective_function("aper0Z", "aper0D")
