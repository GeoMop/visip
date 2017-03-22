Workflow_2 = Workflow()
Function_3 = FunctionAction(
    Inputs=[
        Workflow_2.input()
    ],
    Params=[
        'x1',
        'x2'
    ],
    Expressions=[
        'y1 = 2 * x1 + 2',
        'y2 = 2 * x2 + 3'
    ]
)
Workflow_2.set_config(
    OutputAction=Function_3,
    InputAction=Function_3
)
Calibration_4 = Calibration(
    Inputs=[
        VariableGenerator_1
    ],
    WrappedAction=Workflow_2,
    Parameters=[
        CalibrationParameter(
            name='x1',
            group='pokus',
            bounds=(-10000000000.0, 10000000000.0),
            init_value=1.0,
            offset=0.0,
            scale=1.0,
            fixed=False,
            log_transform=False,
            tied_params=None,
            tied_expression=None
        ),
        CalibrationParameter(
            name='x2',
            group='pokus',
            bounds=(-10000000000.0, 10000000000.0),
            init_value=1.0,
            offset=0.0,
            scale=1.0,
            fixed=False,
            log_transform=False,
            tied_params=None,
            tied_expression=None
        )
    ],
    Observations=[
        CalibrationObservation(
            name='y1',
            group='tunel',
            observation_type=CalibrationObservationType.scalar,
            weight=1.0,
            upper_bound=None,
            lower_bound=None
        ),
        CalibrationObservation(
            name='y2',
            group='tunel',
            observation_type=CalibrationObservationType.scalar,
            weight=1.0,
            upper_bound=None,
            lower_bound=None
        )
    ],
    AlgorithmParameters=[
        CalibrationAlgorithmParameter(
            group='pokus',
            diff_inc_rel=0.01,
            diff_inc_abs=0.0
        )
    ],
    TerminationCriteria=CalibrationTerminationCriteria(
        n_lowest=10,
        tol_lowest=1e-06,
        n_from_lowest=10,
        n_param_change=10,
        tol_rel_param_change=1e-06,
        n_max_steps=100
    ),
    MinimizationMethod='SLSQP',
    BoundsType=CalibrationBoundsType.hard
)