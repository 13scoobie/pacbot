from core.terraform.resources.aws.ecs import ECSServiceResource
from core.terraform.resources.aws.ecs import ECSClusterResource
from core.terraform.resources.misc import NullResource
from core.config import Settings
from resources.pacbot_app import ecs_task_defintions as td
from resources.pacbot_app import alb_target_groups as tg
from resources.vpc.security_group import InfraSecurityGroupResource
from resources.pacbot_app import alb_listener_rules as alr
from resources.pacbot_app.build_ui_and_api import BuildUiAndApis
from resources.pacbot_app.import_db import ImportDbSql
from core.providers.aws.boto3.ecs import stop_all_services_in_a_cluster
import os


class ApplicationECSCluster(ECSClusterResource):
    name = ""


class BaseEcsService:
    desired_count = 1
    launch_type = "FARGATE"
    cluster = ApplicationECSCluster.get_output_attr('id')
    network_configuration_security_groups = [InfraSecurityGroupResource.get_output_attr('id')]
    network_configuration_subnets = Settings.get('VPC')['SUBNETS']
    network_configuration_assign_public_ip = True
    load_balancer_container_port = 80
    tags = None
    # propagate_tags = "SERVICE"  #The new ARN and resource ID format must be enabled to propagate tags


class NginxEcsService(BaseEcsService, ECSServiceResource):
    name = "webapp"
    task_definition = td.NginxEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.NginxALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = td.NginxEcsTaskDefinition.container_name
    DEPENDS_ON = [BuildUiAndApis, alr.ApplicationLoadBalancerListener]


class ConfigEcsService(BaseEcsService, ECSServiceResource):
    name = "config"
    task_definition = td.ConfigEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.ConfigALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "config"
    DEPENDS_ON = [BuildUiAndApis, alr.ConfigALBListenerRule]


class WaitConfigServiceToUp(NullResource):
    DEPENDS_ON = [ConfigEcsService, ImportDbSql]

    def get_provisioners(self):
        '''
        This is to make config service run first as other services has dependancy on it
        '''
        return [{
            'local-exec': {
                'command': "import time; time.sleep(1)",
                'interpreter': [Settings.PYTHON_INTERPRETER, "-c"]
            }
        }]


class AdminEcsService(BaseEcsService, ECSServiceResource):
    name = "admin"
    task_definition = td.AdminEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.AdminALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "admin"
    DEPENDS_ON = [alr.AdminALBListenerRule, WaitConfigServiceToUp]


class ComplianceEcsService(BaseEcsService, ECSServiceResource):
    name = "compliance"
    task_definition = td.ComplianceEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.ComplianceALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "compliance"
    DEPENDS_ON = [alr.ComplianceALBListenerRule, WaitConfigServiceToUp]


# TODO: Commenting this out to use it in future
# class NotificationsEcsService(ECSServiceResource, BaseEcsService):
#     name = "notifications"
#     task_definition = td.NotificationsEcsTaskDefinition.get_output_attr('arn')
#     load_balancer_target_group_arn = tg.NotificationsALBTargetGroup.get_output_attr('arn')
#     load_balancer_container_name = "notifications"
#     DEPENDS_ON = [alr.NotificationsALBListenerRule, WaitConfigServiceToUp]


class StatisticsEcsService(BaseEcsService, ECSServiceResource):
    name = "statistics"
    task_definition = td.StatisticsEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.StatisticsALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "statistics"
    DEPENDS_ON = [alr.StatisticsALBListenerRule, WaitConfigServiceToUp]


class AssetEcsService(BaseEcsService, ECSServiceResource):
    name = "asset"
    task_definition = td.AssetEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.AssetALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "asset"
    DEPENDS_ON = [alr.AssetALBListenerRule, WaitConfigServiceToUp]


class AuthEcsService(BaseEcsService, ECSServiceResource):
    name = "auth"
    task_definition = td.AuthEcsTaskDefinition.get_output_attr('arn')
    load_balancer_target_group_arn = tg.AuthALBTargetGroup.get_output_attr('arn')
    load_balancer_container_name = "auth"
    DEPENDS_ON = [alr.AuthALBListenerRule, WaitConfigServiceToUp]
